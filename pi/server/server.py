from flask import Flask, jsonify, request
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from settings.settings import load_settings
import paho.mqtt.client as mqtt
import json
import uuid
import time
from threading import Timer

app = Flask(__name__)

settings = load_settings()

# InfluxDB
token = settings["influxdb"]["token"]
org = settings["influxdb"]["org"]
url = settings["influxdb"]["url"]
bucket = settings["influxdb"]["bucket"]

# MQTT
mqtt_host = settings["mqtt"]["broker"]
mqtt_port = settings["mqtt"]["port"]

DUS_HISTORY_WINDOW = 5
ENTRY_DISTANCE_THRESHOLD = 60
MOTION_COOLDOWN = 10

system_state = {
    "is_alarm_active": False,
    "is_system_armed": True,
    "people_count": 0,

    "dus_history": {
        "DUS1": [],
        "DUS2": []
    },

    "last_motion_event": {
        "DUS1": 0,
        "DUS2": 0
    },

    "last_dus1_distance": 0,
    "last_dus2_distance": 0,

    "last_ds_readings": {
        "DS1": "",
        "DS2": ""
    },

    "last_dht_readings": {
        "Bedroom DHT": {"temp": 0, "hum": 0},
        "Master Bedroom DHT": {"temp": 0, "hum": 0},
        "Kitchen DHT": {"temp": 0, "hum": 0}
    },
    "dht_names_list": ["Bedroom DHT", "Master Bedroom DHT", "Kitchen DHT"],
    "current_dht_index": 0,

    "entered_pin": "",
    "pin": "1234"
}


def get_all_topics(settings):
    topics = []
    for pi_key in ["PI1", "PI2", "PI3"]:
        if pi_key in settings:
            components = settings[pi_key].get("components", {})
            for comp_id, comp_data in components.items():
                if "topic" in comp_data:
                    topics.append(comp_data["topic"])
    if "mqtt" in settings and "topics" in settings["mqtt"]:
        for t in settings["mqtt"]["topics"].values():
            topics.append(t)
    return list(set(topics))


all_mqtt_topics = get_all_topics(settings)

influxdb_client = InfluxDBClient(url=url, token=token, org=org)

mqtt_client = mqtt.Client(
    client_id=f"flask_influx_{uuid.uuid4()}",
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2
)


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("✅ MQTT connected successfully.")
        for topic in all_mqtt_topics:
            client.subscribe(topic)
            print(f"📡 Subscribed to: {topic}")
        client.subscribe("timer/set")
        client.subscribe("timer/increment")
        print("📡 Subscribed to timer control topics")
    else:
        print(f"❌ MQTT connection failed with result code {rc}")


def on_message(client, userdata, msg):
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
        handle_event(data, msg.topic)
    except Exception as e:
        print(f"⚠️ Error handling MQTT message: {e}")


mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

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


def save_to_influx(data):
    try:
        write_api = influxdb_client.write_api(write_options=SYNCHRONOUS)
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


# --- DUS ISTORIJA ---

def update_dus_history(dus_key, distance):
    now = time.time()
    history = system_state["dus_history"][dus_key]
    history.append({"distance": distance, "timestamp": now})
    system_state["dus_history"][dus_key] = [
        entry for entry in history
        if now - entry["timestamp"] <= DUS_HISTORY_WINDOW + 2
    ]
    print(f"[DEBUG] {dus_key} history updated | distance: {distance:.2f} | entries: {len(system_state['dus_history'][dus_key])}")


def get_recent_min_distance(dus_key):
    now = time.time()
    history = system_state["dus_history"][dus_key]
    recent = [
        entry["distance"]
        for entry in history
        if now - entry["timestamp"] <= DUS_HISTORY_WINDOW
    ]
    if not recent:
        return None
    min_dist = min(recent)
    print(f"[DEBUG] {dus_key} min distance (last {DUS_HISTORY_WINDOW}s): {min_dist:.2f} cm from {len(recent)} readings")
    return min_dist


def determine_entry_or_exit(dus_key):
    min_distance = get_recent_min_distance(dus_key)
    if min_distance is None:
        return None
    return min_distance < ENTRY_DISTANCE_THRESHOLD


def handle_motion_event(dpir_topic, dus_key):
    now = time.time()
    last = system_state["last_motion_event"][dus_key]

    if now - last < MOTION_COOLDOWN:
        print(f"[{dpir_topic}] ⏳ Cooldown aktivan, preskačem event")
        return None

    is_entering = determine_entry_or_exit(dus_key)

    if is_entering is None:
        print(f"[{dpir_topic}] ⚠️  Motion detected but no recent DUS data from {dus_key}")
        return None

    system_state["last_motion_event"][dus_key] = now

    if is_entering:
        system_state["people_count"] += 1
        print(f"[{dpir_topic}] ➡️  Person ENTERING")
        print(f"👥 People in building: {system_state['people_count']}")
        mqtt_client.publish("commands/PI1/DL", json.dumps({"value": True}))
        Timer(10, lambda: mqtt_client.publish("commands/PI1/DL", json.dumps({"value": False}))).start()
    else:
        system_state["people_count"] = max(0, system_state["people_count"] - 1)
        print(f"[{dpir_topic}] ⬅️  Person EXITING")
        print(f"👥 People in building: {system_state['people_count']}")

    mqtt_client.publish("/entries", json.dumps({"people_count": system_state["people_count"]}))
    
    # Direktno upiši u InfluxDB
    save_to_influx({
        "measurement": "entries",
        "simulated": True,
        "runs_on": "flask",
        "name": "People Count",
        "value": system_state["people_count"]
    })

    return is_entering


# --- EVENT HANDLER ---

def handle_event(data, topic):
    value = data.get("value")
    name = data.get("name")

    print(f"[DEBUG] topic: '{topic}' | value: {value}")

    # DUS istorija
    if topic == "pi1/dus1":
        update_dus_history("DUS1", value)
        system_state["last_dus1_distance"] = value

    elif topic == "pi2/dus2":
        update_dus_history("DUS2", value)
        system_state["last_dus2_distance"] = value

    # DPIR detekcija pokreta
    elif topic == "pi1/dpir1" and value == 1:
        entered = handle_motion_event("pi1/dpir1", "DUS1")
        if entered is False and system_state["people_count"] == 0 and system_state["is_system_armed"]:
            activate_alarm()

    elif topic == "pi2/dpir2" and value == 1:
        entered = handle_motion_event("pi2/dpir2", "DUS2")
        if entered is False and system_state["people_count"] == 0 and system_state["is_system_armed"]:
            activate_alarm()

    elif topic == "pi3/dpir3" and value == 1:
        if system_state["people_count"] == 0 and system_state["is_system_armed"]:
            activate_alarm()

    # DS senzori
    elif topic == "pi1/ds1":
        system_state["last_ds_readings"]["DS1"] = value
        if value == 1 and system_state["is_system_armed"]:
            Timer(10, check_alarm_after_delay).start()

    elif topic == "pi2/ds2":
        system_state["last_ds_readings"]["DS2"] = value
        if value == 1 and system_state["is_system_armed"]:
            Timer(10, check_alarm_after_delay).start()

    # Membrane switch – unos PIN-a
    elif topic == "pi1/dms":
        system_state["entered_pin"] += str(value)
        if len(system_state["entered_pin"]) == 4:
            manage_alarm_system()
            system_state["entered_pin"] = ""

    # DHT temperatura i vlažnost
    elif topic in ["pi3/dht1", "pi3/dht2", "pi2/dht3"]:
        measurement = data.get("measurement")
        name = data.get("name")
        if measurement == "Temperature":
            system_state["last_dht_readings"][name]["temp"] = value
        elif measurement == "Humidity":
            system_state["last_dht_readings"][name]["hum"] = value

    # IR daljinski → RGB
    elif topic == "pi3/ir":
        target = "off" if value == "POWER" else value
        mqtt_client.publish("commands/PI3/BRGB", json.dumps({"color": target}))


# --- ALARM LOGIKA ---

def activate_alarm():
    if not system_state["is_alarm_active"]:
        system_state["is_alarm_active"] = True
        mqtt_client.publish("commands/PI1/DB", json.dumps({"value": True}))
        print("🚨 ALARM ACTIVATED")


def deactivate_alarm():
    if system_state["is_alarm_active"]:
        system_state["is_alarm_active"] = False
        mqtt_client.publish("commands/PI1/DB", json.dumps({"value": False}))
        print("✅ ALARM DEACTIVATED")


def arm_system():
    system_state["is_system_armed"] = True
    print("🔒 System ARMED")


def correct_pin():
    return system_state["pin"] == system_state["entered_pin"]


def manage_alarm_system():
    if not system_state["is_system_armed"] and correct_pin():
        Timer(10, arm_system).start()

    if system_state["is_system_armed"] and system_state["is_alarm_active"] and correct_pin():
        system_state["is_system_armed"] = False
        deactivate_alarm()


def check_alarm_after_delay():
    if system_state["is_system_armed"] and not system_state["is_alarm_active"]:
        activate_alarm()


# --- DHT DISPLAY ---

def display_dhts():
    idx = system_state["current_dht_index"]
    dht_name = system_state["dht_names_list"][idx]
    readings = system_state["last_dht_readings"][dht_name]

    payload = {
        "line1": f"{dht_name[:16]}",
        "line2": f"T:{readings['temp']}°C H:{readings['hum']}%"
    }

    mqtt_client.publish("commands/PI3/LCD", json.dumps(payload))
    system_state["current_dht_index"] = (idx + 1) % len(system_state["dht_names_list"])
    Timer(10, display_dhts).start()


# --- API RUTE ---

@app.route('/query', methods=['POST'])
def query_data():
    content = request.json
    query = content.get('query')
    if not query:
        return jsonify({"status": "error", "message": "No query provided"}), 400
    return handle_influx_query(query)


@app.route('/timer/set', methods=['POST'])
def set_timer():
    content = request.json
    seconds = content.get('seconds')
    if seconds is None:
        return jsonify({"status": "error", "message": "No seconds provided"}), 400
    try:
        mqtt_client.publish("timer/set", json.dumps({"seconds": int(seconds)}), qos=1)
        return jsonify({"status": "success", "message": f"Timer set to {seconds} seconds"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/timer/increment', methods=['POST'])
def set_timer_increment():
    content = request.json
    increment = content.get('increment')
    if increment is None:
        return jsonify({"status": "error", "message": "No increment provided"}), 400
    try:
        mqtt_client.publish("timer/increment", json.dumps({"increment": int(increment)}), qos=1)
        return jsonify({"status": "success", "message": f"Button increment set to {increment} seconds"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/system/state', methods=['GET'])
def get_system_state():
    return jsonify({
        "status": "success",
        "data": {
            "people_count": system_state["people_count"],
            "is_alarm_active": system_state["is_alarm_active"],
            "is_system_armed": system_state["is_system_armed"],
        }
    })


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
    display_dhts()
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)