from mqttsn.client import Client, Callback


if __name__ == '__main__':
    aclient = Client("linh", port=1883)
    aclient.register_callback(Callback())
    aclient.connect()

    rc, topic1 = aclient.subscribe("topic1")
    print("topic id for topic1 is", topic1)

    rc, topic2 = aclient.subscribe("topic2")
    print("topic id for topic2 is", topic2)

    aclient.publish(topic1, "aaaa", qos=0)
    aclient.publish(topic2, "bbbb", qos=0)

    aclient.unsubscribe("topic1")

    aclient.publish(topic2, "bbbb", qos=0)
    aclient.publish(topic1, "aaaa", qos=0)

    aclient.disconnect()
