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

import MQTTSN
import socket
import MQTTSNinternal
import thread
import types
import struct
import logging

log = logging.getLogger("mqttsn")


class Callback:
    def __init__(self):
        self.events = []
        self.registered = {}

    def connection_lost(self, cause):
        log.warning(f'Connection Lost: {cause}')
        self.events.append("Disconnected")

    def message_arrived(self, topic_name, payload, qos, retained, msgid):
        log.debug(
            f'Publish Arrived: {topic_name}, {payload}, '
            f'{qos}, {retained}, {msgid}'
        )
        return True

    def delivery_complete(self, msgid):
        log.debug(f'Delivery Complete')

    def advertise(self, address, gwid, duration):
        log.debug(f'Advertise: {address}, {gwid}, {duration}')

    def register(self, topic_id, topic_name):
        self.registered[topic_id] = topic_name


class Client:
    def __init__(self, client_id, host="localhost", port=1883):
        self.client_id = client_id
        self.host = host
        self.port = port
        self.msgid = 1
        self.callback = None
        self.__receiver = None

    def start(self):
        self.sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
            socket.IPPROTO_UDP
        )

        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        mreq = struct.pack("4sl", socket.inet_aton(self.host), socket.INADDR_ANY)

        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        self.start_receiver()

    def stop(self):
        self.stop_receiver()

    def __next_msg_id(self):
        def get_wrapped_msg_id():
            id = self.msg_id + 1
            if id == 65535:
                id = 1
            return id

        if len(self.__receiver.out_msgs) >= 65535:
            raise "No slots left!!"
        else:
            self.msgid = get_wrapped_msg_id()
            while self.msg_id in self.__receiver.out_msgs:
                self.msg_id = get_wrapped_msg_id()
        return self.msg_id

    def register_callback(self, callback):
        self.callback = callback

    def connect(self, cleansession=True):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # self.sock.settimeout(5.0)

        self.sock.connect((self.host, self.port))

        connect = MQTTSN.Connects()
        connect.ClientId = self.client_id
        connect.CleanSession = cleansession
        connect.KeepAliveTimer = 0
        self.sock.send(connect.pack())

        response, address = MQTTSN.unpackPacket(MQTTSN.getPacket(self.sock))
        assert response.mh.MsgType == MQTTSN.CONNACK

        self.start_receiver()

    def start_receiver(self):
        self.__receiver = MQTTSNinternal.Receivers(self.sock)
        if self.callback:
            thread.start_new_thread(self.__receiver, (self.callback,))

    def waitfor(self, msg_type, msg_id=None):
        if self.__receiver:
            msg = self.__receiver.waitfor(msg_type, msg_id)
        else:
            msg = self.__receiver.receive()
            while (msg.mh.msg_type != msg_type and
                    (msg_id is None or msg_id == msg.msg_id)):
                msg = self.__receiver.receive()
        return msg

    def subscribe(self, topic, qos=2):
        subscribe = MQTTSN.Subscribes()
        subscribe.msg_id = self.__next_msg_id()

        if isinstance(topic, types.StringType):
            subscribe.topic_name = topic
            if len(topic) > 2:
                subscribe.flags.topic_id_type = MQTTSN.TOPIC_NORMAL
            else:
                subscribe.flags.topic_id_type = MQTTSN.TOPIC_SHORTNAME
        else:
            subscribe.topic_id = topic  # should be int
            subscribe.flags.topic_id_type = MQTTSN.TOPIC_PREDEFINED

        subscribe.flags.qos = qos
        if self.__receiver:
            self.__receiver.lookfor(MQTTSN.SUBACK)
        self.sock.send(subscribe.pack())
        msg = self.waitfor(MQTTSN.SUBACK, subscribe.msg_id)

        return msg.return_code, msg.topic_id

    def unsubscribe(self, topics):
        unsubscribe = MQTTSN.Unsubscribes()
        unsubscribe.msg_id = self.__next_msg_id()
        unsubscribe.data = topics
        if self.__receiver:
            self.__receiver.lookfor(MQTTSN.UNSUBACK)
        self.sock.send(unsubscribe.pack())
        self.waitfor(MQTTSN.UNSUBACK, unsubscribe.msg_id)

    def register(self, topic_name):
        register = MQTTSN.Registers()
        register.topic_name = topic_name
        if self.__receiver:
            self.__receiver.lookfor(MQTTSN.REGACK)
        self.sock.send(register.pack())
        msg = self.waitfor(MQTTSN.REGACK, register.msg_id)
        return msg.topic_id

    def publish(self, topic, payload, qos=0, retained=False):
        publish = MQTTSN.Publishes()
        publish.flags.qos = qos
        publish.flags.retain = retained
        if isinstance(topic, types.StringType):
            publish.flags.topic_id_type = MQTTSN.TOPIC_SHORTNAME
            publish.topic_name = topic
        else:
            publish.flags.topic_id_type = MQTTSN.TOPIC_NORMAL
            publish.topic_id = topic
        if qos in [-1, 0]:
            publish.msg_id = 0
        else:
            publish.msg_id = self.__next_msg_id()
            log.debug(f'Message ID: {publish.msg_id}')
            self.__receiver.outMsgs[publish.msg_id] = publish
        publish.Data = payload
        self.sock.send(publish.pack())
        return publish.msd_id

    def disconnect(self):
        disconnect = MQTTSN.Disconnects()
        if self.__receiver:
            self.__receiver.lookfor(MQTTSN.DISCONNECT)
        self.sock.send(disconnect.pack())
        self.waitfor(MQTTSN.DISCONNECT)

    def stop_receiver(self):
        self.sock.close()  # this will stop the receiver too
        assert self.__receiver.in_msgs == {}
        assert self.__receiver.out_msgs == {}
        self.__receiver = None

    def receive(self):
        return self.__receiver.receive()


def publish(topic, payload, retained=False, port=1883, host="localhost"):
    publish = MQTTSN.Publishes()
    publish.flags.qos = 3
    publish.flags.retain = retained
    if isinstance(topic, types.StringType):
        if len(topic) > 2:
            publish.flags.topic_id_type = MQTTSN.TOPIC_NORMAL
            publish.topic_id = len(topic)
            payload = topic + payload
        else:
            publish.flags.topic_id_type = MQTTSN.TOPIC_SHORTNAME
            publish.topic_name = topic
    else:
        publish.flags.topic_id_type = MQTTSN.TOPIC_NORMAL
        publish.topic_id = topic
    publish.msg_id = 0
    log.debug(f'payload {payload}')
    publish.Data = payload
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(publish.pack(), (host, port))
    sock.close()
