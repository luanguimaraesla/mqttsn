from .packets import Packets
from .message_headers import MessageHeaders
from .helpers import write_int_16, read_int_16
from .flags import Flags
from .names import UNSUBACK, UNSUBSCRIBE


class Unsubscribes(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(UNSUBSCRIBE)
        self.flags = Flags()
        self.msg_id = 0  # 2 bytes
        self.topic_id = 0  # 2 bytes
        self.topic_name = ""
        if buffer is not None:
            self.unpack(buffer)

    def pack(self):
        buffer = self.flags.pack() + write_int_16(self.msg_id)
        if self.flags.topic_id_type == 0:
            buffer += bytes(self.topic_name.encode('utf-8'))
        elif self.flags.topic_id_type == 1:
            buffer += write_int_16(self.topic_id)
        elif self.flags.topic_id_type == 2:
            buffer += bytes(self.topic_id.encode('utf-8'))
        return self.mh.pack(len(buffer)) + buffer

    def unpack(self, buffer):
        pos = self.mh.unpack(buffer)
        assert self.mh.msg_type == UNSUBSCRIBE
        pos += self.flags.unpack(buffer[pos:])
        self.msg_id = read_int_16(buffer[pos:])
        pos += 2
        self.topic_id = 0
        self.topic_name = ""
        if self.flags.topic_id_type == 0:
            self.topic_name = buffer[pos:self.mh.length]
        elif self.flags.topic_id_type == 1:
            self.topic_id = read_int_16(buffer[pos:])
        elif self.flags.topic_id_type == 3:
            self.topic_id = buffer[pos:pos+2]

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
        return Packets.__eq__(self, packet) and \
                 self.flags == packet.flags and \
                 self.msg_id == packet.msg_id and \
                 self.topic_id == packet.topic_id and \
                 self.topic_name == packet.topic_name


class Unsubacks(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(UNSUBACK)
        self.msg_id = 0
        if buffer is not None:
            self.unpack(buffer)

    def pack(self):
        return self.mh.pack(2) + write_int_16(self.msg_id)

    def unpack(self, buffer):
        pos = self.mh.unpack(buffer)
        assert self.mh.msg_type == UNSUBACK
        self.msg_id = read_int_16(buffer[pos:])

    def __str__(self):
        return f'{self.mh}, msg_id {self.msg_id}'

    def __eq__(self, packet):
        return Packets.__eq__(self, packet) and self.msg_id == packet.msg_id
