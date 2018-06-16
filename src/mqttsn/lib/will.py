from .packets import Packets
from .message_headers import MessageHeaders
from .helpers import write_int_16, read_int_16, chr_
from .flags import Flags
from .names import (
    WILLMSG, WILLTOPIC, WILLMSGREQ, WILLMSGUPD, WILLMSGRESP,
    WILLTOPICREQ, WILLTOPICUPD, WILLTOPICRESP
)


class WillTopicReqs(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(WILLTOPICREQ)
        if buffer is not None:
            self.unpack(buffer)

    def unpack(self, buffer):
        # pos = self.mh.unpack(buffer)
        self.mh.unpack(buffer)
        assert self.mh.msg_type == WILLTOPICREQ


class WillTopics(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(WILLTOPIC)
        self.flags = Flags()
        self.will_topic = ""
        if buffer is not None:
            self.unpack(buffer)

    def pack(self):
        buffer = self.flags.pack() + chr_(self.will_topic)
        return self.mh.pack(len(buffer)) + buffer

    def unpack(self, buffer):
        pos = self.mh.unpack(buffer)
        assert self.mh.msg_type == WILLTOPIC
        pos += self.flags.unpack(buffer[pos:])
        self.will_topic = buffer[pos:self.mh.length]

    def __str__(self):
        return f'{self.mh}, flags {self.flags}, will_topic {self.will_topic}'

    def __eq__(self, packet):
        return Packets.__eq__(self, packet) and \
            self.flags == packet.flags and \
            self.will_topic == packet.will_topic


class WillMsgReqs(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(WILLMSGREQ)
        if buffer is not None:
            self.unpack(buffer)

    def unpack(self, buffer):
        # pos = self.mh.unpack(buffer)
        self.mh.unpack(buffer)
        assert self.mh.msg_type == WILLMSGREQ


class WillMsgs(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(WILLMSG)
        self.will_msg = ""
        if buffer is not None:
            self.unpack(buffer)

    def pack(self):
        return self.mh.pack(len(self.will_msg)) + chr_(self.will_msg)

    def unpack(self, buffer):
        pos = self.mh.unpack(buffer)
        assert self.mh.msg_type == WILLMSG
        self.will_msg = buffer[pos:self.mh.length]

    def __str__(self):
        return f'{self.mh}, will_msg {self.will_msg}'

    def __eq__(self, packet):
        return Packets.__eq__(self, packet) and \
            self.will_msg == packet.will_msg


class WillTopicUpds(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(WILLTOPICUPD)
        self.flags = Flags()
        self.will_topic = ""
        if buffer is not None:
            self.unpack(buffer)

    def pack(self):
        buffer = self.flags.pack() + chr_(self.will_topic)
        return self.mh.pack(len(buffer)) + buffer

    def unpack(self, buffer):
        pos = self.mh.unpack(buffer)
        assert self.mh.msg_type == WILLTOPICUPD
        pos += self.flags.unpack(buffer[pos:])
        self.will_topic = buffer[pos:self.mh.length]

    def __str__(self):
        return f'{self.mh}, flags {self.flags}, will_topic {self.will_topic}'

    def __eq__(self, packet):
        return Packets.__eq__(self, packet) and \
            self.flags == packet.flags and \
            self.will_topic == packet.will_topic


class WillMsgUpds(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(WILLMSGUPD)
        self.will_msg = ""
        if buffer is not None:
            self.unpack(buffer)

    def pack(self):
        return self.mh.pack(len(self.will_msg)) + chr_(self.will_msg)

    def unpack(self, buffer):
        pos = self.mh.unpack(buffer)
        assert self.mh.msg_type == WILLMSGUPD
        self.will_msg = buffer[pos:self.mh.length]

    def __str__(self):
        return f'{self.mh}, will_msg {self.will_msg}'

    def __eq__(self, packet):
        return Packets.__eq__(self, packet) and \
            self.will_msg == packet.will_msg


class WillTopicResps(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(WILLTOPICRESP)
        self.return_code = 0
        if buffer is not None:
            self.unpack(buffer)

    def pack(self):
        buffer = write_int_16(self.return_code)
        return self.mh.pack(len(buffer)) + buffer

    def unpack(self, buffer):
        pos = self.mh.unpack(buffer)
        assert self.mh.msg_type == WILLTOPICRESP
        self.return_code = read_int_16(buffer[pos:])

    def __str__(self):
        return f'{self.mh}, return_code {self.return_code}'

    def __eq__(self, packet):
        return Packets.__eq__(self, packet) and \
            self.return_code == packet.return_code


class WillMsgResps(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(WILLMSGRESP)
        self.return_code = 0
        if buffer is not None:
            self.unpack(buffer)

    def pack(self):
        buffer = write_int_16(self.return_code)
        return self.mh.pack(len(buffer)) + buffer

    def unpack(self, buffer):
        pos = self.mh.unpack(buffer)
        assert self.mh.msg_type == WILLMSGRESP
        self.return_code = read_int_16(buffer[pos:])

    def __str__(self):
        return f'{self.mh}, return_code {self.return_code}'

    def __eq__(self, packet):
        return Packets.__eq__(self, packet) and \
            self.return_code == packet.return_code
