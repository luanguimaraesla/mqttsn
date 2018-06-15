## MQTT-sn Client Examples

```python
if __name__ == "__main__":

    """
    mclient = Client("myclientid", host="225.0.18.83", port=1883)
    mclient.registerCallback(Callback())
    mclient.start()

    publish("long topic name", "qos -1 start", port=1884)

    callback = Callback()

    aclient = Client("myclientid", port=1884)
    aclient.registerCallback(callback)

    aclient.connect()
    aclient.disconnect()

    aclient.connect()
    aclient.subscribe("k ", 2)
    aclient.subscribe("jkjkjkjkj", 2)
    aclient.publish("k ", "qos 0")
    aclient.publish("k ", "qos 1", 1)
    aclient.publish("jkjkjkjkj", "qos 2", 2)
    topicid = aclient.register("jkjkjkjkj")
    #time.sleep(1.0)
    aclient.publish(topicid, "qos 2 - registered topic id", 2)
    #time.sleep(1.0)
    aclient.disconnect()
    publish("long topic name", "qos -1 end", port=1884)

    time.sleep(30)
    mclient.stop()
    """


	aclient = Client("linh", port=1883)
	aclient.registerCallback(Callback())
	aclient.connect()

	rc, topic1 = aclient.subscribe("topic1")
	print "topic id for topic1 is", topic1
	rc, topic2 = aclient.subscribe("topic2")
	print "topic id for topic2 is", topic2
	aclient.publish(topic1, "aaaa", qos=0)
	aclient.publish(topic2, "bbbb", qos=0)
	aclient.unsubscribe("topic1")
	aclient.publish(topic2, "bbbb", qos=0)
	aclient.publish(topic1, "aaaa", qos=0)
	aclient.disconnect()
```

Read more at https://github.com/eclipse/mosquitto.rsmb/
