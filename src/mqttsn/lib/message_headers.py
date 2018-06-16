import logging

from .names import packet_names
from .helpers import write_int_16, read_int_16, chr_

log = logging.getLogger('message_headers')


class MessageHeaders:
    def __init__(self, msg_type):
        self.length = 0
        self.msg_type = msg_type

    def __eq__(self, mh):
        return self.length == mh.length and self.msg_type == mh.msg_type

    def __str__(self):
        """
        Returns:
            printable stresentation of our data
        """
        return f'length {self.length}, {packet_names[self.msg_type]}'

    def pack(self, length):
        """
        Pack data into string buffer ready for transmission down socket
        """
        # length does not yet include the length or msgtype bytes we
        # are going to add
        buffer = self.encode(length) + chr_(self.msg_type)
        return buffer

    def encode(self, length):
        self.length = length + 2
        assert 2 <= self.length <= 65535
        if self.length < 256:
            buffer = chr_(self.length)
            log.debug(f'Encoding length {self.length}')
        else:
            self.length += 2
            buffer = chr_(1) + write_int_16(self.length)
        return buffer

    def unpack(self, buffer):
        """
        Unpack data from string buffer into separate fields
        """
        (self.length, _bytes) = self.decode(buffer)
        self.msg_type = buffer[_bytes]
        return _bytes + 1

    def decode(self, buffer):
        value = buffer[0]
        if value > 1:
            _bytes = 1
        else:
            value = read_int_16(buffer[1:])
            _bytes = 3
        return (value, _bytes)
