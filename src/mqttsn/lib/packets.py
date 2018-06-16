class Packets:
    def __str__(self):
        return str(self.mh)

    def __eq__(self, packet):
        return False if packet is None else self.mh == packet.mh

    def __ne__(self, packet):
        return not self.__eq__(packet)

    def pack(self):
        return self.mh.pack(0)

    def unpack(self):
        raise NotImplementedError
