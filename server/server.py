from flask import Flask, jsonify, request
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from Pi1.settings import load_settings
import paho.mqtt.client as mqtt
import json
import uuid
import time

#Flask service that uses MQTT protocol and writes to INfluxDB, it enables sending HTTP queries 
app = Flask(__name__)

settings = load_settings()
token = settings["influxdb"]["token"]
org = settings["influxdb"]["org"]
url = settings["influxdb"]["url"]
bucket = settings["influxdb"]["bucket"]

mqtt_host = settings["mqtt"]["broker"]
mqtt_port = settings["mqtt"]["port"]
mqtt_topics = settings["mqtt"]["topics"]

influxdb_client = InfluxDBClient(url=url, token=token, org=org)

# Use callback API version 2 to avoid deprecation warning
mqtt_client = mqtt.Client(client_id=f"flask_influx_{uuid.uuid4()}", callback_api_version=mqtt.CallbackAPIVersion.VERSION2)

def on_connect(client, userdata, flags, rc, properties=None):
    print(f"MQTT connected with result code {rc}")
    for topic in mqtt_topics.values():
        client.subscribe(topic)
        print(f"Subscribed to topic: {topic}")

def on_message(client, userdata, msg):
    print(f"Received MQTT message on topic: {msg.topic}")
    try:
        payload = msg.payload.decode("utf-8")
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            data = {
                "measurement": msg.topic,
                "value": payload,
                "simulated": False,
                "runs_on": "unknown",
                "name": "unknown"
            }
        save_to_influx(data)
    except Exception as e:
        print(f"Error handling MQTT message: {e}")

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# Connect with retry logic
max_retries = 5
retry_delay = 2

for attempt in range(max_retries):
    try:
        print(f"Attempting to connect to MQTT broker at {mqtt_host}:{mqtt_port} (attempt {attempt + 1}/{max_retries})...")
        mqtt_client.connect(mqtt_host, mqtt_port, 60)
        mqtt_client.loop_start()
        print("Successfully connected to MQTT broker!")
        break
    except Exception as e:
        if attempt < max_retries - 1:
            print(f"Connection failed: {e}. Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
        else:
            print(f"Failed to connect to MQTT broker after {max_retries} attempts: {e}")
            raise

def save_to_influx(data):
    try:
        write_api = influxdb_client.write_api(write_options=SYNCHRONOUS)
    
        point = (
        Point(data["measurement"])
        .tag("measurement", data['measurement'])
        .tag("simulated", data["simulated"])
        .tag("runs_on", data["runs_on"])
        .tag("name", data["name"])
        .field("value", data["value"])
    )
        write_api.write(bucket=bucket, org=org, record=point)
        print(f"Data written to InfluxDB: {data}")
    except Exception as e:
        print(f"Error writing to InfluxDB: {e}")

def handle_influx_query(query):
    try:
        query_api = influxdb_client.query_api()
        tables = query_api.query(query, org=org)

        container = []
        for table in tables:
            for record in table.records:
                container.append(record.values)

        return jsonify({"status": "success", "data": container})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)