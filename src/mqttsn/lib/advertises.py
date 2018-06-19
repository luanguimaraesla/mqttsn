from .packets import Packets
from .message_headers import MessageHeaders
from .names import ADVERTISE
from .helpers import write_int_16, read_int_16


class Advertises(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(ADVERTISE)
        self.gw_id = 0         # 1 byte
        self.duration = 0  # 2 bytes
        if buffer:
            self.unpack(buffer)

    def pack(self):
        buffer = chr(self.gw_id) + write_int_16(self.duration)
        return self.mh.pack(len(buffer)) + buffer

    def unpack(self, buffer):
        pos = self.mh.unpack(buffer)
        assert self.mh.msg_type == ADVERTISE
        self.gw_id = buffer[pos]
        pos += 1
        self.duration = read_int_16(buffer[pos:])

    def __str__(self):
        return f'{self.mh}, gw_id {self.gw_id}, duration {self.duration}'

    def __eq__(self, packet):
        return Packets.__eq__(self, packet) and \
               self.gw_id == packet.gw_id and \
               self.duration == packet.duration
