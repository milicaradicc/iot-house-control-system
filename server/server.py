from flask import Flask, jsonify, request
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from simulation.settings import load_settings
import paho.mqtt.client as mqtt
import json
import uuid

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

mqtt_client = mqtt.Client(client_id=f"flask_influx_{uuid.uuid4()}")

def on_connect(client, userdata, flags, rc):                    # when connecting is done 
    print(f"MQTT connected with result code {rc}")
    for topic in mqtt_topics.values():
        client.subscribe(topic)                                 #subscribe to all topics
        print(f"Subscribed to topic: {topic}")

def on_message(client, userdata, msg):                          # when recieve message
    print(f"Received MQTT message on topic: {msg.topic}")
    try:
        payload = msg.payload.decode("utf-8")
        try:
            data = json.loads(payload)                          # JSON string -> dict
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

mqtt_client.connect("localhost", 1883, 60)          # connect on MQTT brocker, keep alive 60s
mqtt_client.loop_start()                            # thread that listens messages and call callback functions

def save_to_influx(data):
    try:
        write_api = influxdb_client.write_api(write_options=SYNCHRONOUS)            #
        # point = (
        #     Point(data.get("measurement", "unknown"))
        #     .tag("simulated", str(data.get("simulated", True)))
        #     .tag("runs_on", str(data.get("runs_on", "unknown")))
        #     .tag("name", str(data.get("name", "unknown")))
        #     .field("value", float(data.get("value", 0)))
        # )

    
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

@app.route("/store_data", methods=["POST"])
def store_data_route():
    try:
        data = request.get_json()
        save_to_influx(data)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

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

@app.route("/simple_query", methods=["GET"])
def retrieve_simple_data():
    query = f'''
    from(bucket: "{bucket}")
    |> range(start: -10m)
    |> filter(fn: (r) => r._measurement == "Distance")
    '''
    return handle_influx_query(query)

@app.route("/aggregate_query", methods=["GET"])
def retrieve_aggregate_data():
    query = f'''
    from(bucket: "{bucket}")
    |> range(start: -10m)
    |> filter(fn: (r) => r._measurement == "Distance")
    |> mean(column: "value")
    '''
    return handle_influx_query(query)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
