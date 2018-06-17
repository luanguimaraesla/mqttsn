import logging

from .packets import Packets
from .message_headers import MessageHeaders
from .flags import Flags
from .helpers import write_int_16, read_int_16
from .names import (
    SUBSCRIBE, TOPIC_PREDEFINED, TOPIC_NORMAL,
    TOPIC_SHORTNAME, SUBACK
)


log = logging.getLogger('subscribes')


class Subscribes(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(SUBSCRIBE)
        self.flags = Flags()
        self.msg_id = 0  # 2 bytes
        self.topic_id = 0  # 2 bytes
        self.topic_name = ""
        if buffer is not None:
            self.unpack(buffer)

    def pack(self):
        buffer = self.flags.pack() + write_int_16(self.msg_id)
        if self.flags.topic_id_type == TOPIC_PREDEFINED:
            buffer += write_int_16(self.topic_id)
        elif self.flags.topic_id_type in [TOPIC_NORMAL, TOPIC_SHORTNAME]:
            buffer += bytes(self.topic_name.encode('utf-8'))
        return self.mh.pack(len(buffer)) + buffer

    def unpack(self, buffer):
        pos = self.mh.unpack(buffer)
        assert self.mh.msg_type == SUBSCRIBE
        pos += self.flags.unpack(buffer[pos:])
        self.msg_id = read_int_16(buffer[pos:])
        pos += 2
        self.topic_id = 0
        self.topic_name = ""
        if self.flags.topic_id_type == TOPIC_PREDEFINED:
            self.topic_id = read_int_16(buffer[pos:])
        elif self.flags.topic_id_type in [TOPIC_NORMAL, TOPIC_SHORTNAME]:
            self.topic_name = buffer[pos:pos + 2]

    def __str__(self):
        buffer = f'{self.mh}, flags {self.flags}, msg_id {self.msg_id}'
        if self.flags.topic_id_type == 0:
            buffer += f', topic_name {self.topic_name}'
        elif self.flags.topic_id_type == 1:
            buffer += f', topic_id {self.topic_id}'
        elif self.flags.topic_id_type == 2:
            buffer += f', topic_id {self.topic_id}'
        return buffer

    def __eq__(self, packet):
        if self.flags.topic_id_type == 0:
            rc = self.topic_name == packet.topic_name
        else:
            rc = self.topic_id == packet.topic_id

        return Packets.__eq__(self, packet) and \
            self.flags == packet.flags and \
            self.msg_id == packet.msg_id and rc


class Subacks(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(SUBACK)
        self.flags = Flags()  # 1 byte
        self.topic_id = 0  # 2 bytes
        self.msg_id = 0  # 2 bytes
        self.return_code = 0  # 1 byte
        if buffer is not None:
            self.unpack(buffer)

    def pack(self):
        buffer = self.flags.pack() + write_int_16(self.topic_id) + \
            write_int_16(self.msg_id) + chr(self.return_code)
        return self.mh.pack(len(buffer)) + buffer

    def unpack(self, buffer):
        pos = self.mh.unpack(buffer)
        assert self.mh.msg_type == SUBACK
        pos += self.flags.unpack(buffer[pos:])
        self.topic_id = read_int_16(buffer[pos:])
        pos += 2
        self.msg_id = read_int_16(buffer[pos:])
        pos += 2
        self.return_code = buffer[pos]

    def __str__(self):
        return f'{self.mh}, flags {self.flags}, topic_id {self.topic_id},' \
               f'msg_id {self.msg_id}, return_code {self.return_code}'

    def __eq__(self, packet):
        return Packets.__eq__(self, packet) and \
            self.flags == packet.flags and \
            self.topic_id == packet.topic_id and \
            self.msg_id == packet.msg_id and \
            self.return_code == packet.return_code
