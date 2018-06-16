from mqttsn.client import Client, Callback

import sys


class MyCallback(Callback):
    def message_arrived(self, topic_name, payload, qos, retained, msgid):
        print(f'{self} | topic_name: {topic_name} | payload: {payload} | '
              f'qos {qos} | retained {retained} | msgid {msgid}',
              file=sys.stderr)

        return True


if __name__ == '__main__':
    aclient = Client("linh", port=1883)
    aclient.register_callback(MyCallback())
    aclient.connect()

    rc, topic1 = aclient.subscribe("topic1")
    print("topic id for topic1 is", topic1)

    rc, topic2 = aclient.subscribe("topic2")
    print("topic id for topic2 is", topic2)

    aclient.publish(topic1, "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", qos=0)
    aclient.publish(topic2, "bbbb", qos=0)

    aclient.unsubscribe("topic1")

    aclient.publish(topic2, "bbbb", qos=0)
    aclient.publish(topic1, "aaaa", qos=0)

    aclient.disconnect()
