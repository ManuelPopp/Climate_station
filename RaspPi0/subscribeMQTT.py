from paho.mqtt import client as mqtt_client
import time, random
import argparse

def parseArguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("topic", type = str, \
                        default = "stream/inputs", \
                        help = "Topic to listen to.")
    args = parser.parse_args()
    return args
if __name__ == "__main__":
    args = parseArguments()

client_id = "Raspi0"
username = "Grewia"
password = "Grewia_rogersii"

broker = "localhost"
port = 1883

def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker.")
        else:
            print("Failed to connect, return code %d\n", rc)
    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

def subscribe(client: mqtt_client, topic = None):
    print(f"Subscribing to topic {topic}")
    def on_message(client, userdata, message):
        mssg = str(message.payload.decode("utf-8"))
        print(mssg, flush = True)
    client.subscribe(topic)
    client.on_message = on_message

def run_subscription(topic):
    client = connect_mqtt()
    subscribe(client, topic = topic)
    client.loop_forever()

run_subscription(args.topic)
