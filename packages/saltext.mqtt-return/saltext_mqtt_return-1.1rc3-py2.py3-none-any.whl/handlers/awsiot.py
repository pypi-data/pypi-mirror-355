import logging

import boto3
import json

log = logging.getLogger(__name__)

CLIENT = None


def publish(opts, topic, data, qos=1):
    global CLIENT

    if CLIENT is None:
        CLIENT = boto3.client(
            "iot-data",
            region_name=opts.get("aws_region"),
            endpoint_url=opts.get("endpoint"),
        )

    CLIENT.publish(
        topic=f"{topic}",
        qos=qos,
        # retain=False, #depends on boto version
        payload=bytes(json.dumps(data), "utf-8"),
    )
