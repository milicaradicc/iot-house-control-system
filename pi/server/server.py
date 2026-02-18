from flask import Flask, jsonify, request
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from settings.settings import load_settings
import paho.mqtt.client as mqtt
import json
import uuid
import time
from threading import Timer

# Flask servis koji koristi MQTT protokol i upisuje u InfluxDB
app = Flask(__name__)

# Učitavanje podešavanja
settings = load_settings()

# InfluxDB konfiguracija
token = settings["influxdb"]["token"]
org = settings["influxdb"]["org"]
url = settings["influxdb"]["url"]
bucket = settings["influxdb"]["bucket"]

# MQTT konfiguracija
mqtt_host = settings["mqtt"]["broker"]
mqtt_port = settings["mqtt"]["port"]

system_state = {
    "is_alarm_active": False,
    "is_system_armed": False,
    "people_count": 0,

    "last_dus1_distance": 0,
    "last_dus2_distance": 0,
    "last_dht_readings": {
        "DHT1": "",
        "DHT2": "",
        "DHT3": ""
    },
    "ds1_open_time": None,
    "pin": "1234"
}

# --- DINAMIČKO IZVLAČENJE TOPIKA ---
def get_all_topics(settings):
    topics = []
    # Prolazimo kroz ključeve PI1, PI2, PI3 u JSON-u
    for pi_key in ["PI1", "PI2", "PI3"]:
        if pi_key in settings:
            components = settings[pi_key].get("components", {})
            for comp_id, comp_data in components.items():
                if "topic" in comp_data:
                    topics.append(comp_data["topic"])
    
    # Dodajemo i dodatne topike iz "mqtt" sekcije ako su definisani
    if "mqtt" in settings and "topics" in settings["mqtt"]:
        for t in settings["mqtt"]["topics"].values():
            topics.append(t)
            
    return list(set(topics)) # Uklanjanje duplikata

all_mqtt_topics = get_all_topics(settings)
# ----------------------------------

influxdb_client = InfluxDBClient(url=url, token=token, org=org)

# Koristimo Callback API v2 za Paho MQTT
mqtt_client = mqtt.Client(
    client_id=f"flask_influx_{uuid.uuid4()}", 
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2
)

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"✅ MQTT connected successfully.")
        for topic in all_mqtt_topics:
            client.subscribe(topic)
            print(f"📡 Subscribed to: {topic}")
        
        # Subscribe na timer komandne topike
        client.subscribe("timer/set")
        client.subscribe("timer/increment")
        print(f"📡 Subscribed to timer control topics")
    else:
        print(f"❌ MQTT connection failed with result code {rc}")
        
def on_message(client, userdata, msg):
    print(f"📩 Received MQTT message on topic: {msg.topic}")
    try:
        payload = msg.payload.decode("utf-8")

        try:
            data = json.loads(payload)


        except json.JSONDecodeError:
            # Ako poruka nije JSON, pravimo fallback strukturu
            data = {
                "measurement": msg.topic,
                "value": payload,
                "simulated": False,
                "runs_on": "unknown",
                "name": "unknown"
            }

        save_to_influx(data)
        handle_event(data, msg.topic)


    except Exception as e:
        print(f"⚠️ Error handling MQTT message: {e}")

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# Logika za povezivanje sa pokušajima (Retry logic)
max_retries = 5
retry_delay = 2

for attempt in range(max_retries):
    try:
        print(f"🔄 Attempting MQTT connect {mqtt_host}:{mqtt_port} ({attempt + 1}/{max_retries})...")
        mqtt_client.connect(mqtt_host, mqtt_port, 60)
        mqtt_client.loop_start()
        break
    except Exception as e:
        if attempt < max_retries - 1:
            time.sleep(retry_delay)
        else:
            print(f"🛑 Failed to connect after {max_retries} attempts.")
            # Ne podižemo exception ovde da bi Flask mogao da se pokrene, 
            # ali MQTT neće raditi bez brokera.

def save_to_influx(data):
    try:
        write_api = influxdb_client.write_api(write_options=SYNCHRONOUS)
        
        # Provera postojanja ključeva pre upisa
        point = (
            Point(data.get("measurement", "default_measurement"))
            .tag("simulated", data.get("simulated", False))
            .tag("runs_on", data.get("runs_on", "unknown"))
            .tag("name", data.get("name", "unknown"))
            .field("value", data.get("value", 0))
        )
        write_api.write(bucket=bucket, org=org, record=point)
        print(f"💾 Written to InfluxDB: {data['measurement']} -> {data['value']}")
    except Exception as e:
        print(f"❌ InfluxDB Write Error: {e}")

def handle_event(data, topic):
    value = data.get("value")
    name = data.get("name")
    if topic == "pi1/dpir1"  and value == 1:

        if system_state["last_dus1_distance"] < 60:
            system_state["people_count"] += 1
            system_state["last_dus1_distance"] = value
            mqtt_client.publish("commands/PI1/DL", json.dumps({"value": True}))
            Timer(10, lambda: mqtt_client.publish("commands/PI1/DL", json.dumps({"value": False}))).start()
            print(system_state)

        #ako nema nikoga u prostoriji detektovanje pokreta na nekom rpir pali alarm
        elif topic in ["pi1/dpir1", "pi2/dpir2", "pi3/dpir3"] and value == 1 and system_state["people_count"] == 0:
            activate_alarm()

        # prikazivati temperature tako da se smenjuju ispisi na par sekundi

        elif topic in ["pi3/dht1", "pi3/dht2", "pi2/dht3"] and value == 1 :
            system_state["last_dht_readings"][name] = value
            print(system_state["last_dht_readings"])
            pass

        # uklj isklj preko daljinskog, ali i preko web aplikacije?
        elif topic == "IR" and value == 1:
            pass




def activate_alarm():
    if not system_state["is_alarm_active"]:
        system_state["is_alarm_active"] = True
        mqtt_client.publish("commands/PI1/DB", json.dumps({"value": True}))     # upali db
        print("🚨 ALARM AKTIVIRAN!")

        #poslati u influx
        #obavesti korisnika na aplikaciji

def deactivate_alarm():
    if system_state["is_alarm_active"]:
        system_state["is_alarm_active"] = False
        mqtt_client.publish("commands/PI1/DB", json.dumps({"value": False}))     # ugasi db
        print("🚨 ALARM DEAKTIVIRAN!")


# --- API RUTE ---

@app.route('/query', methods=['POST'])
def query_data():
    content = request.json
    query = content.get('query')
    if not query:
        return jsonify({"status": "error", "message": "No query provided"}), 400
    return handle_influx_query(query)

# Dodati u main.py (Flask servis)

@app.route('/timer/set', methods=['POST'])
def set_timer():
    """Postavlja vreme na štoperici"""
    content = request.json
    seconds = content.get('seconds')
    
    if seconds is None:
        return jsonify({"status": "error", "message": "No seconds provided"}), 400
    
    try:
        # Slanje MQTT komande za postavljanje tajmera
        mqtt_client.publish(
            "timer/set",
            json.dumps({"seconds": int(seconds)}),
            qos=1
        )
        return jsonify({
            "status": "success", 
            "message": f"Timer set to {seconds} seconds"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/timer/increment', methods=['POST'])
def set_timer_increment():
    """Postavlja broj sekundi koje se dodaju pritiskom na dugme"""
    content = request.json
    increment = content.get('increment')
    
    if increment is None:
        return jsonify({"status": "error", "message": "No increment provided"}), 400
    
    try:
        # Slanje MQTT komande za postavljanje incrementa
        mqtt_client.publish(
            "timer/increment",
            json.dumps({"increment": int(increment)}),
            qos=1
        )
        return jsonify({
            "status": "success", 
            "message": f"Button increment set to {increment} seconds"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

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
    # use_reloader=False je bitno da se MQTT klijent ne bi startovao dva puta
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)