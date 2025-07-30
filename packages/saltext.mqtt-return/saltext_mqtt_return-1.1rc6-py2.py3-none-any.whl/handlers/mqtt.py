import paho.mqtt.publish as mqtt_pub
import salt.utils.json


def publish(opts, topic, data, qos=1):
    mqtt_pub.single(
        f"{topic}",
        payload=bytes(salt.utils.json.dumps(data), "utf-8"),
        qos=qos,
        hostname=opts.get("endpoint", ""),
        port=opts.get("port", ""),
        client_id=opts.get("client_id"),
    )
