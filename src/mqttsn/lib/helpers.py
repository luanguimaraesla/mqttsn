from .objects import objects


def write_int_16(length):
    return chr(length // 256) + chr(length % 256)


def read_int_16(buf):
    return ord(buf[0])*256 + ord(buf[1])


def get_packet(a_socket):
    """
    Receive the next packet
    """
    buf, address = a_socket.recvfrom(65535)  # get the first byte fixed header
    print(f'buf {buf} addr {address} ord {buf[0]}')
    if buf == "":
        return None

    length = buf[0]
    if length == 1:
        if buf == "":
            return None
        length = read_int_16(buf[1:])

    return buf, address


def message_type(buf):
    if buf[0] == 1:
        msgtype = buf[3]
    else:
        msgtype = buf[1]
    return msgtype


def writeUTF(a_string):
    return write_int_16(len(a_string)) + a_string


def readUTF(buffer):
    length = read_int_16(buffer)
    return buffer[2:2+length]


def unpack_packet(*args):
    buffer, address = args
    if message_type(buffer) is not None:
        print(f'{buffer} {message_type} {address}')
        packet = objects[message_type(buffer)]()
        packet.unpack(buffer)
    else:
        packet = None
    return packet, address
