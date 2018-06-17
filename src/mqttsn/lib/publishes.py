import logging

from .packets import Packets
from .flags import Flags
from .message_headers import MessageHeaders
from .helpers import write_int_16, read_int_16, chr_
from .names import (
    PUBLISH, TOPIC_PREDEFINED, TOPIC_NORMAL, TOPIC_SHORTNAME, PUBREC,
    PUBREL, PUBCOMP, PUBACK
)

log = logging.getLogger('publishes')


class Publishes(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(PUBLISH)
        self.flags = Flags()
        self.topic_id = 0  # 2 bytes
        self.topic_name = ""
        self.msg_id = 0  # 2 bytes
        self.data = ""
        if buffer is not None:
            self.unpack(buffer)

    def pack(self):
        buffer = self.flags.pack()
        if self.flags.topic_id_type in [TOPIC_NORMAL, TOPIC_PREDEFINED, 3]:
            log.debug(f'Topic id: {self.topic_id}')
            buffer += write_int_16(self.topic_id)
        elif self.flags.topic_id_type == TOPIC_SHORTNAME:
            buffer += bytes((self.topic_name + "    ")[0:2].encode('utf-8'))
        buffer += write_int_16(self.msg_id)

        if isinstance(self.data, str):
            buffer += bytes(self.data.encode('utf-8'))
        elif isinstance(self.data, bytes):
            buffer += self.data
        else:
            raise TypeError('data should be str or bytes')

        return self.mh.pack(len(buffer)) + buffer

    def unpack(self, buffer):
        pos = self.mh.unpack(buffer)
        assert self.mh.msg_type == PUBLISH
        pos += self.flags.unpack(buffer[pos:])

        self.topic_id = 0
        self.topic_name = ""
        if self.flags.topic_id_type in [TOPIC_NORMAL, TOPIC_PREDEFINED]:
            self.topic_id = read_int_16(buffer[pos:])
        elif self.flags.topic_id_type == TOPIC_SHORTNAME:
            self.topic_name = buffer[pos:pos + 2]

        pos += 2
        self.msg_id = read_int_16(buffer[pos:])
        pos += 2
        self.data = buffer[pos:self.mh.length]

    def __str__(self):
        return f'{self.mh}, flags {self.flags}, topic_id {self.topic_id}, ' \
               f'msg_id {self.msg_id}, data {self.data}'

    def __eq__(self, packet):
        return Packets.__eq__(self, packet) and \
            self.flags == packet.flags and \
            self.topic_id == packet.topic_id and \
            self.msg_id == packet.msg_id and \
            self.data == packet.data


class Pubrecs(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(PUBREC)
        self.msg_id = 0
        if buffer is not None:
            self.unpack(buffer)

    def pack(self):
        return self.mh.pack(2) + write_int_16(self.msg_id)

    def unpack(self, buffer):
        pos = self.mh.unpack(buffer)
        assert self.mh.msg_type == PUBREC
        self.msg_id = read_int_16(buffer[pos:])

    def __str__(self):
        return f'{self.mh}, msg_id {self.msg_id}'

    def __eq__(self, packet):
        return Packets.__eq__(self, packet) and self.msg_id == packet.msg_id


class Pubrels(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(PUBREL)
        self.msg_id = 0
        if buffer is not None:
            self.unpack(buffer)

    def pack(self):
        return self.mh.pack(2) + write_int_16(self.msg_id)

    def unpack(self, buffer):
        pos = self.mh.unpack(buffer)
        assert self.mh.msg_type == PUBREL
        self.msg_id = read_int_16(buffer[pos:])

    def __str__(self):
        return f'{self.mh}, msg_id {self.msg_id}'

    def __eq__(self, packet):
        return Packets.__eq__(self, packet) and self.msg_id == packet.msg_id


class Pubcomps(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(PUBCOMP)
        self.msg_id = 0
        if buffer is not None:
            self.unpack(buffer)

    def pack(self):
        return self.mh.pack(2) + write_int_16(self.msg_id)

    def unpack(self, buffer):
        pos = self.mh.unpack(buffer)
        assert self.mh.msg_type == PUBCOMP
        self.msg_id = read_int_16(buffer[pos:])

    def __str__(self):
        return f'{self.mh}, msg_id {self.msg_id}'

    def __eq__(self, packet):
        return Packets.__eq__(self, packet) and self.msg_id == packet.msg_id


class Pubacks(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(PUBACK)
        self.topic_id = 0
        self.msg_id = 0
        self.return_code = 0  # 1 byte
        if buffer is not None:
            self.unpack(buffer)

    def pack(self):
        buffer = write_int_16(self.topic_id) + \
            write_int_16(self.msg_id) + chr_(self.return_code)
        return self.mh.pack(len(buffer)) + buffer

    def unpack(self, buffer):
        pos = self.mh.unpack(buffer)
        assert self.mh.msg_type == PUBACK
        self.topic_id = read_int_16(buffer[pos:])
        pos += 2
        self.msg_id = read_int_16(buffer[pos:])
        pos += 2
        self.return_code = buffer[pos]

    def __str__(self):
        return f'{self.mh}, topic_id {self.topic_id}, msg_id {self.msg_id}, ' \
               f'return_code {self.return_code}'

    def __eq__(self, packet):
        return Packets.__eq__(self, packet) and \
            self.topic_id == packet.topic_id and \
            self.msg_id == packet.msg_id and \
            self.return_code == packet.return_code
