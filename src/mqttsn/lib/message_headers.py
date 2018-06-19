import logging

from .names import packet_names
from .helpers import write_int_16, read_int_16, chr_

log = logging.getLogger('message_headers')
MAX_BUF_SIZE = 65535
SMALL_BUF_SIZE = 256


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

    def pack(self, bufferlen):
        """
        Pack data into string buffer ready for transmission down socket
        """
        self.length = 1  # msg_type byte
        buffer = self.encode_length(bufferlen) + chr_(self.msg_type)
        return buffer

    def encode_length(self, bufferlen):
        """
        Encode buffer length according to MQTT-SN fixed length specification

        Args:
            bufferlen (int):
                payload length

        Returns:
            encoded message length (bytes)

        Specification:
            Should be b'\x01' if message is greater than 255 bytes, and the
            next to bytes should be the full message size, including headers.
            If it is a short message, up to 255 bytes, should be a single byte
            indicating the size of the message.
        """
        length = self.length + bufferlen
        if self._is_short_buffer(length + 1):
            return chr_(length + 1)
        elif self._is_long_buffer(length + 3):
            return chr_(1) + write_int_16(length + 3)
        else:
            raise "Invalid buffer size"

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
            n_bytes = 1
        else:
            value = read_int_16(buffer[1:])
            n_bytes = 3
        return (value, n_bytes)

    def _is_short_buffer(self, size):
        return size < SMALL_BUF_SIZE and size > 2

    def _is_long_buffer(self, size):
        return size < MAX_BUF_SIZE and size >= SMALL_BUF_SIZE
