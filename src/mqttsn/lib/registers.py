from .packets import Packets
from .message_headers import MessageHeaders
from .helpers import write_int_16, read_int_16
from .names import REGISTER, REGACK


class Registers(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(REGISTER)
        self.topic_id = 0
        self.msg_id = 0
        self.topic_name = ""
        if buffer is not None:
            self.unpack(buffer)

    def pack(self):
        buffer = write_int_16(self.topic_id) + \
                         write_int_16(self.msg_id) + self.topic_name
        return self.mh.pack(len(buffer)) + buffer

    def unpack(self, buffer):
        pos = self.mh.unpack(buffer)
        assert self.mh.msg_type == REGISTER
        self.topic_id = read_int_16(buffer[pos:])
        pos += 2
        self.msg_id = read_int_16(buffer[pos:])
        pos += 2
        self.topic_name = buffer[pos:self.mh.length]

    def __str__(self):
        return f'{self.mh}, topic_id {self.topic_id}, msg_id {self.msg_id}, ' \
                     f'topic_name {self.topic_name}'

    def __eq__(self, packet):
        return Packets.__eq__(self, packet) and \
                     self.topic_id == packet.topic_id and \
                     self.msg_id == packet.msg_id and \
                     self.topic_name == packet.topic_name


class Regacks(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(REGACK)
        self.topic_id = 0
        self.msg_id = 0
        self.return_code = 0  # 1 byte
        if buffer is not None:
            self.unpack(buffer)

    def pack(self):
        buffer = write_int_16(self.topic_id) + \
                         write_int_16(self.msg_id) + chr(self.return_code)
        return self.mh.pack(len(buffer)) + buffer

    def unpack(self, buffer):
        pos = self.mh.unpack(buffer)
        assert self.mh.msg_type == REGACK
        self.topic_id = read_int_16(buffer[pos:])
        pos += 2
        self.msg_id = read_int_16(buffer[pos:])
        pos += 2
        self.return_code = ord(buffer[pos])

    def __str__(self):
        return f'{self.mh}, topic_id {self.topic_id}, msg_id {self.msg_id}, ' \
                     f'return_code {self.return_code}'

    def __eq__(self, packet):
        return Packets.__eq__(self, packet) and \
               self.topic_id == packet.topic_id and \
               self.msg_id == packet.msg_id and \
               self.return_code == packet.return_code
