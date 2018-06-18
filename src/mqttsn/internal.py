"""
/******************************************************************************
 * Copyright (c) 2011, 2013 IBM Corp.
 *
 * All rights reserved. This program and the accompanying materials
 * are made available under the terms of the Eclipse Public License v1.0
 * and Eclipse Distribution License v1.0 which accompany this distribution.
 *
 * The Eclipse Public License is available at
 *        http://www.eclipse.org/legal/epl-v10.html
 * and the Eclipse Distribution License is available at
 *     http://www.eclipse.org/org/documents/edl-v10.php.
 *
 * Contributors:
 *        Ian Craggs - initial API and implementation and initial documentation
 *****************************************************************************/
"""

import time
import sys
import socket
import traceback
import logging

from .lib.publishes import Pubacks, Pubrecs, Pubrels, Pubcomps
from .lib.helpers import get_packet, unpack_packet
from .lib.names import (
    PUBACK, REGISTER, PUBREC, PUBREL, PUBCOMP, PUBLISH, ADVERTISE, TOPIC_NORMAL
)


log = logging.getLogger('internal')


class Receivers:
    def __init__(self, socket):
        log.info("Initializing Receiver")
        self.socket = socket
        self.connected = False
        self.observe = None
        self.observed = []

        self.in_msgs = {}
        self.out_msgs = {}

        self.puback = Pubacks()
        self.pubrec = Pubrecs()
        self.pubrel = Pubrels()
        self.pubcomp = Pubcomps()

    def lookfor(self, msg_type):
        self.observe = msg_type

    def waitfor(self, msg_type, msg_id=None):
        msg = None
        count = 0
        while True:
            while len(self.observed) > 0:
                msg = self.observed.pop(0)
                if msg.mh.msg_type == msg_type and \
                   (msg_id is None or msg.msg_id == msg_id):
                    break
                else:
                    msg = None
            if msg is not None:
                break
            time.sleep(0.2)
            count += 1
            if count == 25:
                msg = None
                break
        self.observe = None
        return msg

    def receive(self, callback=None):
        packet = None
        try:
            val = get_packet(self.socket)
            packet, address = unpack_packet(*val)
        except Exception:
            if sys.exc_info()[0] != socket.timeout:
                log.error(f'Unexpected exception {sys.exc_info()}')
                raise sys.exc_info()
        if packet is None:
            time.sleep(0.1)
            return

        log.debug(f'Packet: {packet}')

        if self.observe == packet.mh.msg_type:
            log.debug(f'Observed packet: {packet}')
            self.observed.append(packet)

        elif packet.mh.msg_type == ADVERTISE:
            if hasattr(callback, "advertise"):
                callback.advertise(address, packet.gw_id, packet.duration)

        elif packet.mh.msg_type == REGISTER:
            if callback and hasattr(callback, "register"):
                callback.register(packet.topic_id, packet.topic_name)

        elif packet.mh.msg_type == PUBACK:
            log.debug("Check if we are expecting a puback")
            if packet.msg_id in self.out_msgs and \
               self.out_msgs[packet.msg_id].flags.qos == 1:
                del self.out_msgs[packet.msg_id]
                if hasattr(callback, "published"):
                    callback.published(packet.msg_id)
            else:
                raise Exception(
                    f'No qos 1 message with message id {packet.msg_id} sent'
                )

        elif packet.mh.msg_type == PUBREC:
            if packet.msg_id in self.out_msgs:
                self.pubrel.msg_id = packet.msg_id
                self.socket.send(self.pubrel.pack())
            else:
                raise Exception(
                    'PUBREC received for unknown msg_id: {packet.msg_id}'
                )

        elif packet.mh.msg_type == PUBREL:
            log.debug("Release qos 2 publication to client, & send PUBCOMP")
            msgid = packet.msg_id
            if msgid not in self.in_msgs:
                pass  # what should we do here?
            else:
                pub = self.in_msgs[packet.msg_id]
                if callback is None or \
                    callback.message_arrived(
                        pub.topic_name, pub.data, 2,
                        pub.flags.retain, pub.msg_id):
                    del self.in_msgs[packet.msg_id]
                    self.pubcomp.msg_id = packet.msg_id
                    self.socket.send(self.pubcomp.pack())
                if callback is None:
                    return (pub.topic_name, pub.data, 2,
                            pub.flags.retain, pub.msg_id)

        elif packet.mh.msg_type == PUBCOMP:
            """
            Finished with this message id
            """
            if packet.msg_id in self.out_msgs:
                del self.out_msgs[packet.msg_id]
                if hasattr(callback, "published"):
                    callback.published(packet.msg_id)
            else:
                raise Exception(
                    f'PUBCOMP received for unknown msg_id: {packet.msg_id}'
                )

        elif packet.mh.msg_type == PUBLISH:
            """
            Finished with this message id
            """
            if packet.flags.qos in [0, 3]:
                qos = packet.flags.qos
                topicname = packet.topic_name.decode('utf-8')
                data = packet.data
                if qos == 3:
                    qos = -1
                    # [FIXME] TOPIC_NORMAL is a workaround to this problem
                    # it was wrong implemented in the original library
                    if packet.flags.topic_id_type == TOPIC_NORMAL:
                        topicname = packet.data[:packet.topic_id]
                        data = packet.data[packet.topic_id:]
                if callback is None:
                    return (topicname, data, qos,
                            packet.flags.retain, packet.msg_id)
                else:
                    callback.message_arrived(
                        topicname, data, qos,
                        packet.flags.retain, packet.msg_id
                    )
            elif packet.flags.qos == 1:
                if callback is None:
                    return (packet.topic_name, packet.data, 1,
                            packet.flags.retain, packet.msg_id)
                else:
                    if callback.message_arrived(
                       packet.topic_name, packet.data, 1,
                       packet.flags.retain, packet.msg_id):

                        self.puback.msg_id = packet.msg_id
                        self.socket.send(self.puback.pack())
            elif packet.flags.qos == 2:
                self.in_msgs[packet.msg_id] = packet
                self.pubrec.msg_id = packet.msg_id
                self.socket.send(self.pubrec.pack())

        else:
            raise Exception(f'Unexpected packet {packet}')
        return packet

    def __call__(self, callback):
        try:
            while True:
                self.receive(callback)
        except Exception:
            if sys.exc_info()[0] != socket.error:
                log.error(f"Unexpected exception {sys.exc_info()}")
                traceback.print_exc()
