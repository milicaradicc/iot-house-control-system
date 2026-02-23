from flask import Flask, jsonify, request
from flask_cors import CORS
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from settings.settings import load_settings
import paho.mqtt.client as mqtt
import json
import uuid
import time
from threading import Timer

app = Flask(__name__)
CORS(app)

settings = load_settings()

token = settings["influxdb"]["token"]
org = settings["influxdb"]["org"]
url = settings["influxdb"]["url"]
bucket = settings["influxdb"]["bucket"]

mqtt_host = settings["mqtt"]["broker"]
mqtt_port = settings["mqtt"]["port"]

DUS_HISTORY_WINDOW = 5
ENTRY_DISTANCE_THRESHOLD = 60
MOTION_COOLDOWN = 10
DOOR_OPEN_ALARM_DELAY = 5

system_state = {
    "is_alarm_active": False,
    "is_system_armed": True,
    "people_count": 0,
    "dus_history": {"DUS1": [], "DUS2": []},
    "last_motion_event": {"DUS1": 0, "DUS2": 0},
    "last_dus1_distance": None,
    "last_dus2_distance": None,
    "last_ds_readings": {"DS1": None, "DS2": None},
    "ds_open_since": {"DS1": None, "DS2": None},
    "ds_alarm_active": {"DS1": False, "DS2": False},
    "last_dht_readings": {
        "Bedroom DHT": {"temp": None, "hum": None},
        "Master Bedroom DHT": {"temp": None, "hum": None},
        "Kitchen DHT": {"temp": None, "hum": None}
    },
    "dht_names_list": ["Bedroom DHT", "Master Bedroom DHT", "Kitchen DHT"],
    "current_dht_index": 0,
    "last_dpir": {"DPIR1": 0, "DPIR2": 0, "DPIR3": 0},
    "last_ir": None,
    "last_gsg": None,
    "current_rgb": "off",
    "last_dl": False,
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
        for t in [
            "pi3/dht1/temp", "pi3/dht1/humidity",
            "pi3/dht2/temp", "pi3/dht2/humidity",
            "pi2/dht3/temp", "pi2/dht3/humidity",
        ]:
            client.subscribe(t)
            print(f"📡 Subscribed to: {t}")
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


# --- DUS HISTORY ---

def update_dus_history(dus_key, distance):
    now = time.time()
    history = system_state["dus_history"][dus_key]
    history.append({"distance": distance, "timestamp": now})
    system_state["dus_history"][dus_key] = [
        entry for entry in history
        if now - entry["timestamp"] <= DUS_HISTORY_WINDOW + 2
    ]
    print(f"[DEBUG] {dus_key} history | distance: {distance:.2f} | entries: {len(system_state['dus_history'][dus_key])}")


def get_recent_min_distance(dus_key):
    now = time.time()
    history = system_state["dus_history"][dus_key]
    recent = [e["distance"] for e in history if now - e["timestamp"] <= DUS_HISTORY_WINDOW]
    if not recent:
        return None
    min_dist = min(recent)
    print(f"[DEBUG] {dus_key} min distance (last {DUS_HISTORY_WINDOW}s): {min_dist:.2f} cm")
    return min_dist


def determine_entry_or_exit(dus_key):
    min_distance = get_recent_min_distance(dus_key)
    if min_distance is None:
        return None
    return min_distance < ENTRY_DISTANCE_THRESHOLD


# --- MOTION HANDLING ---

def _auto_off_dl():
    system_state["last_dl"] = False
    mqtt_client.publish("commands/PI1/DL", json.dumps({"value": False}))


def handle_motion_event(dpir_topic, dus_key):
    now = time.time()
    last = system_state["last_motion_event"][dus_key]

    if now - last < MOTION_COOLDOWN:
        print(f"[{dpir_topic}] ⏳ Cooldown active, skipping event")
        return None

    is_entering = determine_entry_or_exit(dus_key)

    if is_entering is None:
        print(f"[{dpir_topic}] ⚠️  Motion detected but no recent DUS data from {dus_key}")
        return None

    system_state["last_motion_event"][dus_key] = now

    if is_entering:
        system_state["people_count"] += 1
        print(f"[{dpir_topic}] ➡️  Person ENTERING | 👥 {system_state['people_count']}")
        system_state["last_dl"] = True
        mqtt_client.publish("commands/PI1/DL", json.dumps({"value": True}))
        Timer(10, _auto_off_dl).start()
    else:
        system_state["people_count"] = max(0, system_state["people_count"] - 1)
        print(f"[{dpir_topic}] ⬅️  Person EXITING | 👥 {system_state['people_count']}")

    mqtt_client.publish("/entries", json.dumps({"people_count": system_state["people_count"]}))

    save_to_influx({
        "measurement": "entries",
        "simulated": True,
        "runs_on": "flask",
        "name": "People Count",
        "value": system_state["people_count"]
    })

    return is_entering


# --- DOOR SENSOR ALARM LOGIC ---

def check_ds_alarm(ds_key):
    open_since = system_state["ds_open_since"][ds_key]
    if open_since is None:
        return
    if time.time() - open_since >= DOOR_OPEN_ALARM_DELAY:
        print(f"[{ds_key}] 🚪 Door open for more than {DOOR_OPEN_ALARM_DELAY}s → ALARM")
        system_state["ds_alarm_active"][ds_key] = True
        activate_alarm()


def any_ds_alarm_active():
    return any(system_state["ds_alarm_active"].values())


# --- EVENT HANDLER ---

def handle_event(data, topic):
    value = data.get("value")

    print(f"[DEBUG] topic: '{topic}' | value: {value}")

    if topic == "pi1/dus1":
        update_dus_history("DUS1", value)
        system_state["last_dus1_distance"] = value

    elif topic == "pi2/dus2":
        update_dus_history("DUS2", value)
        system_state["last_dus2_distance"] = value

    elif topic == "pi1/dpir1" and value == 1:
        system_state["last_dpir"]["DPIR1"] = time.time()
        entered = handle_motion_event("pi1/dpir1", "DUS1")
        if entered is False and system_state["people_count"] == 0 and system_state["is_system_armed"]:
            activate_alarm()

    elif topic == "pi2/dpir2" and value == 1:
        system_state["last_dpir"]["DPIR2"] = time.time()
        entered = handle_motion_event("pi2/dpir2", "DUS2")
        if entered is False and system_state["people_count"] == 0 and system_state["is_system_armed"]:
            activate_alarm()

    elif topic == "pi3/dpir3" and value == 1:
        system_state["last_dpir"]["DPIR3"] = time.time()
        if system_state["people_count"] == 0 and system_state["is_system_armed"]:
            activate_alarm()

    elif topic == "pi2/gsg":
        movement = data.get("movement")
        magnitude = data.get("value")
        system_state["last_gsg"] = magnitude
        if movement >= 1:
            print(f"[GSG] 🚰 Faucet movement detected! Magnitude: {magnitude}g")
            activate_alarm()

    elif topic == "pi1/ds1":
        system_state["last_ds_readings"]["DS1"] = value
        if value == 1:
            if system_state["ds_open_since"]["DS1"] is None:
                system_state["ds_open_since"]["DS1"] = time.time()
                print(f"[DS1] 🚪 Door opened — waiting {DOOR_OPEN_ALARM_DELAY}s...")
                Timer(DOOR_OPEN_ALARM_DELAY, lambda: check_ds_alarm("DS1")).start()
        else:
            system_state["ds_open_since"]["DS1"] = None
            if system_state["ds_alarm_active"]["DS1"]:
                system_state["ds_alarm_active"]["DS1"] = False
                print("[DS1] 🚪 Door closed")
                if not any_ds_alarm_active():
                    deactivate_alarm()

    elif topic == "pi2/ds2":
        system_state["last_ds_readings"]["DS2"] = value
        if value == 1:
            if system_state["ds_open_since"]["DS2"] is None:
                system_state["ds_open_since"]["DS2"] = time.time()
                print(f"[DS2] 🚪 Door opened — waiting {DOOR_OPEN_ALARM_DELAY}s...")
                Timer(DOOR_OPEN_ALARM_DELAY, lambda: check_ds_alarm("DS2")).start()
        else:
            system_state["ds_open_since"]["DS2"] = None
            if system_state["ds_alarm_active"]["DS2"]:
                system_state["ds_alarm_active"]["DS2"] = False
                print("[DS2] 🚪 Door closed")
                if not any_ds_alarm_active():
                    deactivate_alarm()

    elif topic == "pi1/dl":
        system_state["last_dl"] = bool(value)

    elif topic == "pi1/dms":
        system_state["entered_pin"] += str(value)
        if len(system_state["entered_pin"]) == 4:
            manage_alarm_system()
            system_state["entered_pin"] = ""

    # DHT — subtopic format
    elif topic == "pi3/dht1/temp":
        system_state["last_dht_readings"]["Bedroom DHT"]["temp"] = value
    elif topic == "pi3/dht1/humidity":
        system_state["last_dht_readings"]["Bedroom DHT"]["hum"] = value
    elif topic == "pi3/dht2/temp":
        system_state["last_dht_readings"]["Master Bedroom DHT"]["temp"] = value
    elif topic == "pi3/dht2/humidity":
        system_state["last_dht_readings"]["Master Bedroom DHT"]["hum"] = value
    elif topic == "pi2/dht3/temp":
        system_state["last_dht_readings"]["Kitchen DHT"]["temp"] = value
    elif topic == "pi2/dht3/humidity":
        system_state["last_dht_readings"]["Kitchen DHT"]["hum"] = value

    # DHT — fallback stari format sa measurement poljem
    elif topic in ["pi3/dht1", "pi3/dht2", "pi2/dht3"]:
        measurement = data.get("measurement")
        dht_map = {
            "pi3/dht1": "Bedroom DHT",
            "pi3/dht2": "Master Bedroom DHT",
            "pi2/dht3": "Kitchen DHT",
        }
        dht_name = dht_map.get(topic)
        if dht_name:
            if measurement == "Temperature":
                system_state["last_dht_readings"][dht_name]["temp"] = value
            elif measurement == "Humidity":
                system_state["last_dht_readings"][dht_name]["hum"] = value

    elif topic == "pi3/ir":
        system_state["last_ir"] = value
        target = "off" if value == "POWER" else value
        mqtt_client.publish("commands/PI3/BRGB", json.dumps({"color": target}))


# --- ALARM LOGIC ---

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


def correct_pin(entered):
    return system_state["pin"] == entered


def manage_alarm_system(entered_pin):
    """
    Upravljanje alarmom na osnovu unesenog PIN-a.
    - Ako je PIN tačan i alarm je aktivan → ugasi alarm i disarm sistem
    - Ako je PIN tačan i sistem je disarmed → arm za 10s
    - Ako je PIN netačan → ne radi ništa
    """
    if correct_pin(entered_pin):
        if system_state["is_alarm_active"]:
            system_state["is_system_armed"] = False
            deactivate_alarm()
            print("✅ Correct PIN — alarm deactivated, system disarmed")
        elif not system_state["is_system_armed"]:
            Timer(10, arm_system).start()
            print("🔒 Correct PIN — arming system in 10s")
        else:
            print("ℹ️ Correct PIN — system already armed and no alarm active")
    else:
        print("❌ Wrong PIN entered")


# --- DHT LCD DISPLAY ---

def display_dhts():
    idx = system_state["current_dht_index"]
    dht_name = system_state["dht_names_list"][idx]
    readings = system_state["last_dht_readings"][dht_name]
    payload = {
        "line1": f"{dht_name[:16]}",
        "line2": f"T:{readings['temp']}C H:{readings['hum']}%"
    }
    mqtt_client.publish("commands/PI3/LCD", json.dumps(payload))
    system_state["current_dht_index"] = (idx + 1) % len(system_state["dht_names_list"])
    Timer(10, display_dhts).start()


# --- API ROUTES ---

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


@app.route('/system/sensors', methods=['GET'])
def get_sensors():
    now = time.time()
    dpir1_active = (now - system_state["last_dpir"]["DPIR1"]) < 10 if system_state["last_dpir"]["DPIR1"] else False
    dpir2_active = (now - system_state["last_dpir"]["DPIR2"]) < 10 if system_state["last_dpir"]["DPIR2"] else False
    dpir3_active = (now - system_state["last_dpir"]["DPIR3"]) < 10 if system_state["last_dpir"]["DPIR3"] else False
    return jsonify({
        "status": "success",
        "data": {
            "ds1": system_state["last_ds_readings"]["DS1"],
            "ds2": system_state["last_ds_readings"]["DS2"],
            "dus1": system_state["last_dus1_distance"],
            "dus2": system_state["last_dus2_distance"],
            "dpir1": dpir1_active,
            "dpir2": dpir2_active,
            "dpir3": dpir3_active,
            "dl": system_state["last_dl"],
            "ir": system_state["last_ir"],
            "gsg": system_state["last_gsg"],
            "rgb": system_state["current_rgb"],
            "dht": system_state["last_dht_readings"],
        }
    })


@app.route('/alarm/pin', methods=['POST'])
def submit_pin():
    content = request.json
    pin = str(content.get('pin', ''))

    if len(pin) != 4 or not pin.isdigit():
        return jsonify({"status": "error", "message": "PIN mora imati 4 cifre"}), 400

    for digit in pin:
        mqtt_client.publish("pi1/dms", json.dumps({
            "measurement": "pi1/dms",
            "value": digit,
            "simulated": False,
            "runs_on": "flask",
            "name": "DMS"
        }), qos=1)

    mqtt_client.publish("alarm/pin", json.dumps({"pin": pin}), qos=1)

    manage_alarm_system(pin)

    is_correct = correct_pin(pin)
    return jsonify({
        "status": "success",
        "message": "PIN prihvaćen — alarm deaktiviran" if (is_correct and system_state["is_alarm_active"]) else
                   "PIN prihvaćen — sistem se naoružava za 10s" if (is_correct and not system_state["is_system_armed"]) else
                   "PIN prihvaćen" if is_correct else
                   "Pogrešan PIN",
        "correct": is_correct,
        "alarm_active": system_state["is_alarm_active"],
        "system_armed": system_state["is_system_armed"],
    })

@app.route('/rgb/set', methods=['POST'])
def set_rgb():
    content = request.json
    color = content.get('color', 'off')
    system_state["current_rgb"] = color
    mqtt_client.publish("commands/PI3/BRGB", json.dumps({"color": color}))
    return jsonify({"status": "success", "message": f"RGB set to {color}"})


@app.route('/dl/set', methods=['POST'])
def set_dl():
    content = request.json
    value = bool(content.get('value', False))
    system_state["last_dl"] = value
    mqtt_client.publish("commands/PI1/DL", json.dumps({"value": value}))
    return jsonify({"status": "success", "message": f"DL set to {value}"})


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


@app.route('/query', methods=['POST'])
def query_data():
    content = request.json
    query = content.get('query')
    if not query:
        return jsonify({"status": "error", "message": "No query provided"}), 400
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