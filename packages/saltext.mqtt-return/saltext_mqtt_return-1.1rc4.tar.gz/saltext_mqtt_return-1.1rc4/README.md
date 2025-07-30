# mqtt_return

A useful Salt Event returner for publishing messages to MQTT or AWS IoT

## Quickstart

To get started with your new project:

    # Create a new venv
    python3 -m venv env --prompt mqtt_return
    source env/bin/activate

    # On mac, you may need to upgrade pip
    python -m pip install --upgrade pip

    # On WSL or some flavors of linux you may need to install the `enchant`
    # library in order to build the docs
    sudo apt-get install -y enchant

    # Install extension + test/dev/doc dependencies into your environment
    python -m pip install -e .[tests,dev,docs]

    # Run tests!
    python -m nox -e tests-3

    # skip requirements install for next time
    export SKIP_REQUIREMENTS_INSTALL=1

    # Build the docs, serve, and view in your web browser:
    python -m nox -e docs && (cd docs/_build/html; python -m webbrowser localhost:8000; python -m http.server; cd -)

    # Run the example function
    salt-call --local mqtt_return.example_function text="Happy Hacking!"


## Configuration

For publishing to a standard MQTT broker

```yaml
event_return: [mqtt_return]

returner.mqtt_return.output: mqtt

returner.mqtt_return.endpoint: mqtt
returner.mqtt_return.port: 1883
returner.mqtt_return.topic_prefix: "example/prefix"
```

For publishing to AWS IoT Core MQTT broker using boto3 and the iot-data client

```yaml
event_return: [mqtt_return]

returner.mqtt_return.output: awsiot

returner.mqtt_return.endpoint: https://example.iot.amazonaws.com
returner.mqtt_return.topic_prefix: "example/prefix"
returner.mqtt_return.aws_access_key_id: "aaaaa"
returner.mqtt_return.aws_secret_access_key: "aaaaa"
```


## Topic Re-writing

Allows you to re-write the topics with Regex and Python Substr

For example to remove the `salt/` prefix from the topics:

```yaml
returner.mqtt_return.topic_rewrite_regex: "salt/"
returner.mqtt_return.topic_rewrite_replace: ""
```
