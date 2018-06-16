from .helpers import chr_


class Flags:
    def __init__(self):
        self.dup = False          # 1 bit
        self.qos = 0              # 2 bits
        self.retain = False       # 1 bit
        self.will = False         # 1 bit
        self.clean_session = True  # 1 bit
        self.topic_id_type = 0      # 2 bits

    def __eq__(self, flags):
        return self.dup == flags.dup and \
            self.qos == flags.qos and \
            self.retain == flags.retain and \
            self.will == flags.will and \
            self.clean_session == flags.clean_session and \
            self.topic_id_type == flags.topic_id_type

    def __ne__(self, flags):
        return not self.__eq__(flags)

    def __str__(self):
        """
        Returns:
            printable representation of data
        """
        return f'< dup {self.dup}, qos {self.qos}, retain {self.retain}, ' \
               f'will {self.will}, clean_session {self.clean_session}, ' \
               f'topic_id_type {self.topic_id_type} >'

    def pack(self):
        """
        Pack data into string buffer ready for transmission down socket
        """
        return chr_(
            (self.dup << 7) |
            (self.qos << 5) |
            (self.retain << 4) |
            (self.will << 3) |
            (self.clean_session << 2) |
            self.topic_id_type
        )

    def unpack(self, buffer):
        """
        Unpack data from string buffer into separate fields
        """
        b0 = buffer[0]
        self.dup = ((b0 >> 7) & 0x01) == 1
        self.qos = (b0 >> 5) & 0x03
        self.retain = ((b0 >> 4) & 0x01) == 1
        self.will = ((b0 >> 3) & 0x01) == 1
        self.clean_session = ((b0 >> 2) & 0x01) == 1
        self.topic_id_type = (b0 & 0x03)

        return 1
