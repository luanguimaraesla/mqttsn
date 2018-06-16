from .packets import Packets
from .names import DISCONNECT
from .helpers import write_int_16, read_int_16
from .message_headers import MessageHeaders


class Disconnects(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(DISCONNECT)
        self.duration = None
        if buffer is not None:
            self.unpack(buffer)

    def pack(self):
        if self.duration:
            buf = self.mh.pack(2) + write_int_16(self.duration)
        else:
            buf = self.mh.pack(0)
        return buf

    def unpack(self, buffer):
        pos = self.mh.unpack(buffer)
        assert self.mh.msg_type == DISCONNECT
        buf = buffer[pos:self.mh.length]
        if buf == b'':
            self.duration = None
        else:
            self.duration = read_int_16(buffer[pos:])

    def __str__(self):
        buf = str(self.mh)
        if self.duration:
            buf += f', duration {self.duration}'
        return buf

    def __eq__(self, packet):
        return Packets.__eq__(self, packet) and \
            self.duration == packet.duration
