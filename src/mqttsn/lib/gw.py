from .packets import Packets
from .message_headers import MessageHeaders
from .helpers import write_int_16, read_int_16, chr_
from .names import SEARCHGW, GWINFO


class SearchGWs(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(SEARCHGW)
        self.radius = 0
        if buffer:
            self.unpack(buffer)

    def pack(self):
        buffer = write_int_16(self.radius)
        buffer = self.mh.pack(len(buffer)) + buffer
        return buffer

    def unpack(self, buffer):
        pos = self.mh.unpack(buffer)
        assert self.mh.msg_type == SEARCHGW
        self.radius = read_int_16(buffer[pos:])

    def __str__(self):
        return f'{self.mh}, radius {self.radius}'


class GWInfos(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(GWINFO)
        self.gw_id = 0    # 1 byte
        self.gw_add = None  # optional
        if buffer:
            self.unpack(buffer)

    def pack(self):
        buffer = chr_(self.gw_id)
        if self.gw_add:
            buffer += self.gw_add
        buffer = self.mh.pack(len(buffer)) + buffer
        return buffer

    def unpack(self, buffer):
        pos = self.mh.unpack(buffer)
        assert self.mh.msg_type == GWINFO
        self.gw_id = buffer[pos]
        pos += 1
        if pos >= self.mh.length:
            self.gw_add = None
        else:
            self.gw_add = buffer[pos:]

    def __str__(self):
        buf = f'{self.mh} radius {self.gw_id}'
        if self.gw_add:
            buf += f' gw_add {self.gw_add}'
        return buf
