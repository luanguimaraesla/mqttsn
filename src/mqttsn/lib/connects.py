from .packets import Packets
from .message_headers import MessageHeaders
from .names import CONNECT, CONNACK
from .flags import Flags
from .helpers import write_int_16, read_int_16, chr_


class Connects(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(CONNECT)
        self.flags = Flags()
        self.protocol_id = 1
        self.duration = 30
        self.client_id = ""
        if buffer is not None:
            self.unpack(buffer)

    def pack(self):
        buffer = self.flags.pack()
        buffer += chr_(self.protocol_id)
        buffer += write_int_16(self.duration)
        buffer += self.client_id
        return self.mh.pack(len(buffer)) + buffer

    def unpack(self, buffer):
        buffer = buffer.decode('utf-8')
        pos = self.mh.unpack(buffer)
        assert self.mh.msg_type == CONNECT
        pos += self.flags.unpack(buffer[pos])
        self.protocol_id = buffer[pos]
        pos += 1
        self.duration = read_int_16(buffer[pos:])
        pos += 2
        self.client_id = buffer[pos:]

    def __str__(self):
        return f'{self.mh}, flags {self.flags}, protocol_id ' \
               f'{self.protocol_id}, duration {self.duration}, ' \
               f'client_id {self.client_id}'

    def __eq__(self, packet):
        rc = Packets.__eq__(self, packet) and \
            self.flags == packet.flags and \
            self.protocol_id == packet.protocol_id and \
            self.duration == packet.duration and \
            self.client_id == packet.client_id
        return rc


class Connacks(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(CONNACK)
        self.return_code = 0  # 1 byte
        if buffer is not None:
            self.unpack(buffer)

    def pack(self):
        buffer = chr(self.return_code)
        return self.mh.pack(len(buffer)) + buffer

    def unpack(self, buffer):
        pos = self.mh.unpack(buffer)
        assert self.mh.msg_type == CONNACK
        self.return_code = buffer[pos]

    def __str__(self):
        return f'{self.mh}, return_code {self.return_code}'

    def __eq__(self, packet):
        return Packets.__eq__(self, packet) and \
            self.return_code == packet.return_code
