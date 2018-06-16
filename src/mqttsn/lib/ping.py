from .packets import Packets
from .names import PINGREQ, PINGRESP
from .message_headers import MessageHeaders
from .helpers import chr_


class Pingreqs(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(PINGREQ)
        self.client_id = None
        if buffer is not None:
            self.unpack(buffer)

    def pack(self):
        if self.client_id:
            buf = self.mh.pack(len(self.client_id)) + chr_(self.client_id)
        else:
            buf = self.mh.pack(0)
        return buf

    def unpack(self, buffer):
        pos = self.mh.unpack(buffer)
        assert self.mh.msg_type == PINGREQ
        self.client_id = buffer[pos:self.mh.length]
        if self.client_id == '':
            self.client_id = None

    def __str__(self):
        buf = str(self.mh)
        if self.client_id:
            buf += f', client_id {self.client_id}'
        return buf

    def __eq__(self, packet):
        return Packets.__eq__(self, packet) and \
            self.client_id == packet.client_id


class Pingresps(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(PINGRESP)
        if buffer is not None:
            self.unpack(buffer)

    def unpack(self, buffer):
        # pos = self.mh.unpack(buffer)
        self.mh.unpack(buffer)
        assert self.mh.msg_type == PINGRESP
