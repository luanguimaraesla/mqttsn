"""
/*******************************************************************************
 * Copyright (c) 2011, 2013 IBM Corp.
 *
 * All rights reserved. This program and the accompanying materials
 * are made available under the terms of the Eclipse Public License v1.0
 * and Eclipse Distribution License v1.0 which accompany this distribution.
 *
 * The Eclipse Public License is available at
 *    http://www.eclipse.org/legal/epl-v10.html
 * and the Eclipse Distribution License is available at
 *   http://www.eclipse.org/org/documents/edl-v10.php.
 *
 * Contributors:
 *    Ian Craggs - initial API and implementation and/or initial documentation
 *******************************************************************************/
"""

# Low-level protocol interface for MQTTs

import logging

log = logging.getLogger('mqttsn')

# Message types
ADVERTISE, SEARCHGW, GWINFO, reserved, \
    CONNECT, CONNACK, \
    WILLTOPICREQ, WILLTOPIC, WILLMSGREQ, WILLMSG, \
    REGISTER, REGACK, \
    PUBLISH, PUBACK, PUBCOMP, PUBREC, PUBREL, reserved1, \
    SUBSCRIBE, SUBACK, UNSUBSCRIBE, UNSUBACK, \
    PINGREQ, PINGRESP, DISCONNECT, reserved2, \
    WILLTOPICUPD, WILLTOPICRESP, WILLMSGUPD, WILLMSGRESP = range(30)

packet_names = [
    "ADVERTISE", "SEARCHGW", "GWINFO", "reserved",
    "CONNECT", "CONNACK",
    "WILLTOPICREQ", "WILLTOPIC", "WILLMSGREQ", "WILLMSG",
    "REGISTER", "REGACK",
    "PUBLISH", "PUBACK", "PUBCOMP", "PUBREC", "PUBREL", "reserved",
    "SUBSCRIBE", "SUBACK", "UNSUBSCRIBE", "UNSUBACK",
    "PINGREQ", "PINGRESP", "DISCONNECT", "reserved",
    "WILLTOPICUPD", "WILLTOPICRESP", "WILLMSGUPD", "WILLMSGRESP"
]

topic_id_type_names = ["NORMAL", "PREDEFINED", "SHORT_NAME"]
TOPIC_NORMAL, TOPIC_PREDEFINED, TOPIC_SHORTNAME = range(3)


def write_int_16(length):
    return chr(length / 256) + chr(length % 256)


def read_int_16(buf):
    return ord(buf[0])*256 + ord(buf[1])


def get_packet(a_socket):
    """
    Receive the next packet
    """
    buf, address = a_socket.recvfrom(65535)  # get the first byte fixed header
    if buf == "":
        return None

    length = ord(buf[0])
    if length == 1:
        if buf == "":
            return None
        length = read_int_16(buf[1:])

    return buf, address


def message_type(buf):
    if ord(buf[0]) == 1:
        msgtype = ord(buf[3])
    else:
        msgtype = ord(buf[1])
    return msgtype


class Flags:
    def __init__(self):
        self.dup = False          # 1 bit
        self.qos = 0              # 2 bits
        self.retain = False       # 1 bit
        self.will = False         # 1 bit
        self.clean_sessioin = True  # 1 bit
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
        buffer = (
            chr(
                (self.dup << 7) |
                (self.qos << 5) |
                (self.retain << 4) |
                (self.will << 3) |
                (self.clean_session << 2) |
                self.topic_id_type
            )
        )

        return buffer

    def unpack(self, buffer):
        """
        Unpack data from string buffer into separate fields
        """
        b0 = ord(buffer[0])
        self.dup = ((b0 >> 7) & 0x01) == 1
        self.qos = (b0 >> 5) & 0x03
        self.retain = ((b0 >> 4) & 0x01) == 1
        self.will = ((b0 >> 3) & 0x01) == 1
        self.clean_session = ((b0 >> 2) & 0x01) == 1
        self.topic_id_type = (b0 & 0x03)

        return 1


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
        buffer = self.encode(length) + chr(self.msg_type)
        return buffer

    def encode(self, length):
        self.length = length + 2
        assert 2 <= self.length <= 65535
        if self.length < 256:
            buffer = chr(self.length)
            log.debug(f'Encoding length {self.length}')
        else:
            self.length += 2
            buffer = chr(1) + write_int_16(self.length)
        return buffer

    def unpack(self, buffer):
        """
        Unpack data from string buffer into separate fields
        """
        (self.length, bytes) = self.decode(buffer)
        self.msg_type = ord(buffer[bytes])
        return bytes + 1

    def decode(self, buffer):
        value = ord(buffer[0])
        if value > 1:
            bytes = 1
        else:
            value = read_int_16(buffer[1:])
            bytes = 3
        return (value, bytes)


def writeUTF(a_string):
    return write_int_16(len(a_string)) + a_string


def readUTF(buffer):
    length = read_int_16(buffer)
    return buffer[2:2+length]


class Packets:
    def pack(self):
        return self.mh.pack(0)

    def __str__(self):
        return str(self.mh)

    def __eq__(self, packet):
        return False if packet is None else self.mh == packet.mh

    def __ne__(self, packet):
        return not self.__eq__(packet)


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
        self.gw_id = ord(buffer[pos])
        pos += 1
        self.duration = read_int_16(buffer[pos:])

    def __str__(self):
        return f'{self.mh}, gw_id {self.gw_id}, duration {self.duration}'

    def __eq__(self, packet):
        return Packets.__eq__(self, packet) and \
               self.gw_id == packet.gw_id and \
               self.duration == packet.duration


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
        buffer = chr(self.gw_id)
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


class Connects(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(CONNECT)
        self.flags = Flags()
        self.protocol_id = 1
        self.duration = 30
        self.client_id = ""
        if buffer is not None:
            self.unpack(buffer)

    def pack(self):
        buffer = self.flags.pack() + chr(self.protocol_id) + \
                         write_int_16(self.duration) + self.client_id
        return self.mh.pack(len(buffer)) + buffer

    def unpack(self, buffer):
        pos = self.mh.unpack(buffer)
        assert self.mh.msg_type == CONNECT
        pos += self.flags.unpack(buffer[pos])
        self.protocol_id = ord(buffer[pos])
        pos += 1
        self.duration = read_int_16(buffer[pos:])
        pos += 2
        self.client_id = buffer[pos:]

    def __str__(self):
        return f'{self.mh}, flags {self.flags}, protocol_id ' \
               f'{self.protocol_id}, duration {self.duration}, ' \
               f'client_id {self.client_id}'

    def __eq__(self, packet):
        rc = Packets.__eq__(self, packet) and \
             self.flags == packet.flags and \
             self.protocol_id == packet.protocol_id and \
             self.duration == packet.duration and \
             self.client_id == packet.client_id
        return rc


class Connacks(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(CONNACK)
        self.return_code = 0  # 1 byte
        if buffer is not None:
            self.unpack(buffer)

    def pack(self):
        buffer = chr(self.return_code)
        return self.mh.pack(len(buffer)) + buffer

    def unpack(self, buffer):
        pos = self.mh.unpack(buffer)
        assert self.mh.msg_type == CONNACK
        self.return_code = ord(buffer[pos])

    def __str__(self):
        return f'{self.mh}, return_code {self.return_code}'

    def __eq__(self, packet):
        return Packets.__eq__(self, packet) and \
                     self.return_code == packet.return_code


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
        buffer = self.flags.pack() + self.will_topic
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
        return self.mh.pack(len(self.will_msg)) + self.will_msg

    def unpack(self, buffer):
        pos = self.mh.unpack(buffer)
        assert self.mh.msg_type == WILLMSG
        self.will_msg = buffer[pos:self.mh.length]

    def __str__(self):
        return f'{self.mh}, will_msg {self.will_msg}'

    def __eq__(self, packet):
        return Packets.__eq__(self, packet) and \
                     self.will_msg == packet.will_msg


class Registers(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(REGISTER)
        self.topic_id = 0
        self.msg_id = 0
        self.topic_name = ""
        if buffer is not None:
            self.unpack(buffer)

    def pack(self):
        buffer = write_int_16(self.topic_id) + \
                         write_int_16(self.msg_id) + self.topic_name
        return self.mh.pack(len(buffer)) + buffer

    def unpack(self, buffer):
        pos = self.mh.unpack(buffer)
        assert self.mh.msg_type == REGISTER
        self.topic_id = read_int_16(buffer[pos:])
        pos += 2
        self.msg_id = read_int_16(buffer[pos:])
        pos += 2
        self.topic_name = buffer[pos:self.mh.length]

    def __str__(self):
        return f'{self.mh}, topic_id {self.topic_id}, msg_id {self.msg_id}, ' \
                     f'topic_name {self.topic_name}'

    def __eq__(self, packet):
        return Packets.__eq__(self, packet) and \
                     self.topic_id == packet.topic_id and \
                     self.msg_id == packet.msg_id and \
                     self.topic_name == packet.topic_name


class Regacks(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(REGACK)
        self.topic_id = 0
        self.msg_id = 0
        self.return_code = 0  # 1 byte
        if buffer is not None:
            self.unpack(buffer)

    def pack(self):
        buffer = write_int_16(self.topic_id) + \
                         write_int_16(self.msg_id) + chr(self.return_code)
        return self.mh.pack(len(buffer)) + buffer

    def unpack(self, buffer):
        pos = self.mh.unpack(buffer)
        assert self.mh.msg_type == REGACK
        self.topic_id = read_int_16(buffer[pos:])
        pos += 2
        self.msg_id = read_int_16(buffer[pos:])
        pos += 2
        self.return_code = ord(buffer[pos])

    def __str__(self):
        return f'{self.mh}, topic_id {self.topic_id}, msg_id {self.msg_id}, ' \
                     f'return_code {self.return_code}'

    def __eq__(self, packet):
        return Packets.__eq__(self, packet) and \
               self.topic_id == packet.topic_id and \
               self.msg_id == packet.msg_id and \
               self.return_code == packet.return_code


class Publishes(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(PUBLISH)
        self.flags = Flags()
        self.topic_id = 0  # 2 bytes
        self.topic_name = ""
        self.msg_id = 0  # 2 bytes
        self.data = ""
        if buffer is not None:
            self.unpack(buffer)

    def pack(self):
        buffer = self.flags.pack()
        if self.flags.topic_id_type in [TOPIC_NORMAL, TOPIC_PREDEFINED, 3]:
            log.debug(f'Topic id: {self.topic_id}')
            buffer += write_int_16(self.topic_id)
        elif self.flags.topic_id_type == TOPIC_SHORTNAME:
            buffer += (self.topic_name + "    ")[0:2]
        buffer += write_int_16(self.msg_id) + self.data
        return self.mh.pack(len(buffer)) + buffer

    def unpack(self, buffer):
        pos = self.mh.unpack(buffer)
        assert self.mh.msg_type == PUBLISH
        pos += self.flags.unpack(buffer[pos:])

        self.topic_id = 0
        self.topic_name = ""
        if self.flags.topic_id_type in [TOPIC_NORMAL, TOPIC_PREDEFINED]:
            self.topic_id = read_int_16(buffer[pos:])
        elif self.flags.topic_id_type == TOPIC_SHORTNAME:
            self.topic_name = buffer[pos:pos+2]
        pos += 2
        self.msg_id = read_int_16(buffer[pos:])
        pos += 2
        self.data = buffer[pos:self.mh.length]

    def __str__(self):
        return f'{self.mh}, flags {self.flags}, topic_id {self.topic_id}, ' \
               f'msg_id {self.msg_id}, data {self.data}'

    def __eq__(self, packet):
        return Packets.__eq__(self, packet) and \
               self.flags == packet.flags and \
               self.topic_id == packet.topic_id and \
               self.msg_id == packet.msg_id and \
               self.data == packet.data


class Pubacks(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(PUBACK)
        self.topic_id = 0
        self.msg_id = 0
        self.return_code = 0  # 1 byte
        if buffer is not None:
            self.unpack(buffer)

    def pack(self):
        buffer = write_int_16(self.topic_id) + \
                         write_int_16(self.msg_id) + chr(self.return_code)
        return self.mh.pack(len(buffer)) + buffer

    def unpack(self, buffer):
        pos = self.mh.unpack(buffer)
        assert self.mh.msg_type == PUBACK
        self.topic_id = read_int_16(buffer[pos:])
        pos += 2
        self.msg_id = read_int_16(buffer[pos:])
        pos += 2
        self.return_code = ord(buffer[pos])

    def __str__(self):
        return f'{self.mh}, topic_id {self.topic_id}, msg_id {self.msg_id}, ' \
               f'return_code {self.return_code}'

    def __eq__(self, packet):
        return Packets.__eq__(self, packet) and \
                     self.topic_id == packet.topic_id and \
                     self.msg_id == packet.msg_id and \
                     self.return_code == packet.return_code


class Pubrecs(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(PUBREC)
        self.msg_id = 0
        if buffer is not None:
            self.unpack(buffer)

    def pack(self):
        return self.mh.pack(2) + write_int_16(self.msg_id)

    def unpack(self, buffer):
        pos = self.mh.unpack(buffer)
        assert self.mh.msg_type == PUBREC
        self.msg_id = read_int_16(buffer[pos:])

    def __str__(self):
        return f'{self.mh}, msg_id {self.msg_id}'

    def __eq__(self, packet):
        return Packets.__eq__(self, packet) and self.msg_id == packet.msg_id


class Pubrels(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(PUBREL)
        self.msg_id = 0
        if buffer is not None:
            self.unpack(buffer)

    def pack(self):
        return self.mh.pack(2) + write_int_16(self.msg_id)

    def unpack(self, buffer):
        pos = self.mh.unpack(buffer)
        assert self.mh.msg_type == PUBREL
        self.msg_id = read_int_16(buffer[pos:])

    def __str__(self):
        return f'{self.mh}, msg_id {self.msg_id}'

    def __eq__(self, packet):
        return Packets.__eq__(self, packet) and self.msg_id == packet.msg_id


class Pubcomps(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(PUBCOMP)
        self.msg_id = 0
        if buffer is not None:
            self.unpack(buffer)

    def pack(self):
        return self.mh.pack(2) + write_int_16(self.msg_id)

    def unpack(self, buffer):
        pos = self.mh.unpack(buffer)
        assert self.mh.msg_type == PUBCOMP
        self.msg_id = read_int_16(buffer[pos:])

    def __str__(self):
        return f'{self.mh}, msg_id {self.msg_id}'

    def __eq__(self, packet):
        return Packets.__eq__(self, packet) and self.msg_id == packet.msg_id


class Subscribes(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(SUBSCRIBE)
        self.flags = Flags()
        self.msg_id = 0  # 2 bytes
        self.topic_id = 0  # 2 bytes
        self.topic_name = ""
        if buffer is not None:
            self.unpack(buffer)

    def pack(self):
        buffer = self.flags.pack() + write_int_16(self.msg_id)
        if self.flags.topic_id_type == TOPIC_PREDEFINED:
            buffer += write_int_16(self.topic_id)
        elif self.flags.topic_id_type in [TOPIC_NORMAL, TOPIC_SHORTNAME]:
            buffer += self.topic_name
        return self.mh.pack(len(buffer)) + buffer

    def unpack(self, buffer):
        pos = self.mh.unpack(buffer)
        assert self.mh.msg_type == SUBSCRIBE
        pos += self.flags.unpack(buffer[pos:])
        self.msg_id = read_int_16(buffer[pos:])
        pos += 2
        self.topic_id = 0
        self.topic_name = ""
        if self.flags.topic_id_type == TOPIC_PREDEFINED:
            self.topic_id = read_int_16(buffer[pos:])
        elif self.flags.topic_id_type in [TOPIC_NORMAL, TOPIC_SHORTNAME]:
            self.topic_name = buffer[pos:pos+2]

    def __str__(self):
        buffer = f'{self.mh}, flags {self.flags}, msg_id {self.msg_id}'
        if self.flags.topic_id_type == 0:
            buffer += f', topic_name {self.topic_name}'
        elif self.flags.topic_id_type == 1:
            buffer += f', topic_id {self.topic_id}'
        elif self.flags.topic_id_type == 2:
            buffer += f', topic_id {self.topic_id}'
        return buffer

    def __eq__(self, packet):
        if self.flags.topic_id_type == 0:
            rc = self.topic_name == packet.topic_name
        else:
            rc = self.topic_id == packet.topic_id

        return Packets.__eq__(self, packet) and \
            self.flags == packet.flags and \
            self.msg_id == packet.msg_id and rc


class Subacks(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(SUBACK)
        self.flags = Flags()  # 1 byte
        self.topic_id = 0  # 2 bytes
        self.msg_id = 0  # 2 bytes
        self.return_code = 0  # 1 byte
        if buffer is not None:
            self.unpack(buffer)

    def pack(self):
        buffer = self.flags.pack() + write_int_16(self.topic_id) + \
                         write_int_16(self.msg_id) + chr(self.return_code)
        return self.mh.pack(len(buffer)) + buffer

    def unpack(self, buffer):
        pos = self.mh.unpack(buffer)
        assert self.mh.msg_type == SUBACK
        pos += self.flags.unpack(buffer[pos:])
        self.topic_id = read_int_16(buffer[pos:])
        pos += 2
        self.msg_id = read_int_16(buffer[pos:])
        pos += 2
        self.return_code = ord(buffer[pos])

    def __str__(self):
        return f'{self.mh}, flags {self.flags}, topic_id {self.topic_id},' \
                     f'msg_id {self.msg_id}, return_code {self.return_code}'

    def __eq__(self, packet):
        return Packets.__eq__(self, packet) and \
                     self.flags == packet.flags and \
                     self.topic_id == packet.topic_id and \
                     self.msg_id == packet.msg_id and \
                     self.return_code == packet.return_code


class Unsubscribes(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(UNSUBSCRIBE)
        self.flags = Flags()
        self.msg_id = 0  # 2 bytes
        self.topic_id = 0  # 2 bytes
        self.topic_name = ""
        if buffer is not None:
            self.unpack(buffer)

    def pack(self):
        buffer = self.flags.pack() + write_int_16(self.msg_id)
        if self.flags.topic_id_type == 0:
            buffer += self.topic_name
        elif self.flags.topic_id_type == 1:
            buffer += write_int_16(self.topic_id)
        elif self.flags.topic_id_type == 2:
            buffer += self.topic_id
        return self.mh.pack(len(buffer)) + buffer

    def unpack(self, buffer):
        pos = self.mh.unpack(buffer)
        assert self.mh.msg_type == UNSUBSCRIBE
        pos += self.flags.unpack(buffer[pos:])
        self.msg_id = read_int_16(buffer[pos:])
        pos += 2
        self.topic_id = 0
        self.topic_name = ""
        if self.flags.topic_id_type == 0:
            self.topic_name = buffer[pos:self.mh.length]
        elif self.flags.topic_id_type == 1:
            self.topic_id = read_int_16(buffer[pos:])
        elif self.flags.topic_id_type == 3:
            self.topic_id = buffer[pos:pos+2]

    def __str__(self):
        buffer = f'{self.mh}, flags {self.flags}, msg_id {self.msg_id}'
        if self.flags.topic_id_type == 0:
            buffer += f', topic_name {self.topic_name}'
        elif self.flags.topic_id_type == 1:
            buffer += f', topic_id {self.topic_id}'
        elif self.flags.topic_id_type == 2:
            buffer += f', topic_id {self.topic_id}'
        return buffer

    def __eq__(self, packet):
        return Packets.__eq__(self, packet) and \
                 self.flags == packet.flags and \
                 self.msg_id == packet.msg_id and \
                 self.topic_id == packet.topic_id and \
                 self.topic_name == packet.topic_name


class Unsubacks(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(UNSUBACK)
        self.msg_id = 0
        if buffer is not None:
            self.unpack(buffer)

    def pack(self):
        return self.mh.pack(2) + write_int_16(self.msg_id)

    def unpack(self, buffer):
        pos = self.mh.unpack(buffer)
        assert self.mh.msg_type == UNSUBACK
        self.msg_id = read_int_16(buffer[pos:])

    def __str__(self):
        return f'{self.mh}, msg_id {self.msg_id}'

    def __eq__(self, packet):
        return Packets.__eq__(self, packet) and self.msg_id == packet.msg_id


class Pingreqs(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(PINGREQ)
        self.client_id = None
        if buffer is not None:
            self.unpack(buffer)

    def pack(self):
        if self.client_id:
            buf = self.mh.pack(len(self.client_id)) + self.client_id
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
        if buf == '':
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


class WillTopicUpds(Packets):
    def __init__(self, buffer=None):
        self.mh = MessageHeaders(WILLTOPICUPD)
        self.flags = Flags()
        self.will_topic = ""
        if buffer is not None:
            self.unpack(buffer)

    def pack(self):
        buffer = self.flags.pack() + self.will_topic
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
        return self.mh.pack(len(self.will_msg)) + self.will_msg

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


objects = [Advertises, SearchGWs, GWInfos, None,
           Connects, Connacks,
           WillTopicReqs, WillTopics, WillMsgReqs, WillMsgs,
           Registers, Regacks,
           Publishes, Pubacks, Pubcomps, Pubrecs, Pubrels, None,
           Subscribes, Subacks, Unsubscribes, Unsubacks,
           Pingreqs, Pingresps, Disconnects, None,
           WillTopicUpds, WillTopicResps, WillMsgUpds, WillMsgResps]


def unpack_packet(*args):
    buffer, address = args
    if message_type(buffer) is not None:
        packet = objects[message_type(buffer)]()
        packet.unpack(buffer)
    else:
        packet = None
    return packet, address
