from flask import Flask, jsonify, request
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import paho.mqtt.client as mqtt
import json
import uuid  # za unikatan MQTT client_id

app = Flask(__name__)

token = "KpIredGkJhRy2TK5KW1URMr_QfGDxBsNvyqTKCnSw-1SdH-EtlMWAOfvdpnKTMrfdVKunTGLR8xQRCNfJis_2A=="
org = "ftn"
url = "http://localhost:8086"
bucket = "example_bucket"

influxdb_client = InfluxDBClient(url=url, token=token, org=org)

mqtt_client = mqtt.Client(client_id=f"flask_influx_{uuid.uuid4()}")  # unikatan client_id
mqtt_client.connect("localhost", 1883, 60)

mqtt_client.loop_start()

def on_connect(client, userdata, flags, rc):
    print(f"MQTT connected with result code {rc}")
    client.subscribe("Distance")  # pretplata na temu

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode("utf-8"))
        save_to_influx(data)
    except Exception as e:
        print(f"Error handling MQTT message: {e}")

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

def save_to_influx(data):
    try:
        write_api = influxdb_client.write_api(write_options=SYNCHRONOUS)
        point = (
            Point(data["measurement"])
            .tag("simulated", str(data.get("simulated", True)))
            .tag("runs_on", str(data.get("runs_on", "unknown")))
            .tag("name", str(data.get("name", "unknown")))
            .field("measurement", float(data["value"]))
        )
        write_api.write(bucket=bucket, org=org, record=point)
        print(f"Data written to Influx: {data}")
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
    |> mean(column: "_value")
    '''
    return handle_influx_query(query)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
