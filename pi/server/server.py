import random

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

DUS_HISTORY_WINDOW = 8          # FIX: povećano sa 5 → 8s da uhvati batch delay
ENTRY_DISTANCE_THRESHOLD = 60
MOTION_COOLDOWN = 2             # FIX: smanjeno sa 10 → 2s, realno za jednu osobu
DOOR_OPEN_ALARM_DELAY = 5

ARM_PIN = "4321"

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
    "pin": "1234",
    # Alarm reason tracking
    "alarm_reason": None,
    "alarm_triggers": [],
    "alarm_activated_at": None,
    # Kitchen timer
    "timer_seconds": 0,
    "timer_running": False,
    "timer_started_at": None,
    "timer_initial": 0,
    "timer_btn_increment": 10,
    "timer_expired": False,
    # Grace period — PIN unesen dok su vrata otvorena, ne pali alarm
    "ds_grace_period": {"DS1": False, "DS2": False},
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
        client.subscribe("pi2/btn")
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
        print(f"[DEBUG] {dus_key} — nema podataka u prozoru od {DUS_HISTORY_WINDOW}s")
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

def handle_motion_event(dpir_topic, dus_key):
    now = time.time()
    last = system_state["last_motion_event"][dus_key]
    elapsed_since_last = now - last

    if elapsed_since_last < MOTION_COOLDOWN:
        print(f"[{dpir_topic}] ⏳ Cooldown aktivan ({elapsed_since_last:.1f}s < {MOTION_COOLDOWN}s) — skip")
        return None

    is_entering = determine_entry_or_exit(dus_key)

    if is_entering is None:
        print(f"[{dpir_topic}] ⚠️  Motion detektovan ali nema DUS podataka u prozoru od {DUS_HISTORY_WINDOW}s")
        # FIX: ne troši cooldown ako nema DUS podataka — ne ažuriraj last_motion_event
        return None

    # FIX: ažuriraj cooldown tek nakon uspješne odluke
    system_state["last_motion_event"][dus_key] = now

    # FIX: očisti historiju nakon odluke da stari podaci ne utiču na sljedeći event
    system_state["dus_history"][dus_key] = []
    print(f"[{dpir_topic}] 🧹 DUS historija očišćena nakon odluke")

    if is_entering:
        system_state["people_count"] += 1
        print(f"[{dpir_topic}] ➡️  ULAZ | 👥 {system_state['people_count']}")
    else:
        system_state["people_count"] = max(0, system_state["people_count"] - 1)
        print(f"[{dpir_topic}] ⬅️  IZLAZ | 👥 {system_state['people_count']}")

    mqtt_client.publish("/entries", json.dumps({"people_count": system_state["people_count"]}))
    save_to_influx({
        "measurement": "people_count",
        "value": system_state["people_count"],
        "simulated": False,
        "runs_on": "flask",
        "name": "PeopleCounter"
    })
    return is_entering


# --- DOOR SENSOR ALARM LOGIC ---

def check_ds_alarm(ds_key):
    """
    Poziva se nakon DOOR_OPEN_ALARM_DELAY sekundi od otvaranja vrata.
    Ako su vrata još uvijek otvorena aktivira alarm.
    Ako je u međuvremenu unesen ispravan PIN (grace period), alarm se ne pali.
    """
    open_since = system_state["ds_open_since"][ds_key]
    if open_since is None:
        return

    # Grace period — korisnik je unio PIN dok su vrata bila otvorena
    if system_state["ds_grace_period"][ds_key]:
        print(f"[{ds_key}] Grace period aktivan — PIN unesen, alarm se ne aktivira")
        system_state["ds_grace_period"][ds_key] = False
        return

    elapsed = time.time() - open_since
    if elapsed >= DOOR_OPEN_ALARM_DELAY:
        print(f"[{ds_key}] Vrata otvorena {elapsed:.1f}s -> ALARM")
        system_state["ds_alarm_active"][ds_key] = True
        activate_alarm(
            reason=f"Vrata {ds_key} otvorena duze od {DOOR_OPEN_ALARM_DELAY} sekundi",
            sensors=[ds_key]
        )
    else:
        remaining = DOOR_OPEN_ALARM_DELAY - elapsed + 0.2
        print(f"[{ds_key}] Timer prerano okidnuo (proslo {elapsed:.1f}s), retry za {remaining:.1f}s")
        Timer(remaining, lambda: check_ds_alarm(ds_key)).start()


def any_ds_alarm_active():
    return any(system_state["ds_alarm_active"].values())


# --- ALARM LOGIC ---

def activate_alarm(reason=None, sensors=None):
    if not system_state["is_system_armed"]:
        print(f"[ALARM] Sistem nije armed — alarm se ne aktivira (razlog: {reason})")
        return
    if not system_state["is_alarm_active"]:
        system_state["is_alarm_active"] = True
        system_state["alarm_reason"] = reason or "Nepoznat uzrok"
        system_state["alarm_triggers"] = sensors or []
        system_state["alarm_activated_at"] = time.time()
        mqtt_client.publish("commands/PI1/DB", json.dumps({"value": True}))
        print(f"🚨 ALARM ACTIVATED | Razlog: {reason} | Senzori: {sensors}")
    else:
        # Alarm već aktivan — dodaj novi trigger ako postoji
        if sensors:
            for s in sensors:
                if s not in system_state["alarm_triggers"]:
                    system_state["alarm_triggers"].append(s)
        print(f"[ALARM] već aktivan, dodani senzori: {sensors}")


def deactivate_alarm():
    if system_state["is_alarm_active"]:
        system_state["is_alarm_active"] = False
        system_state["alarm_reason"] = None
        system_state["alarm_triggers"] = []
        system_state["alarm_activated_at"] = None
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
    - Ako je PIN 4321 → arm sistem za 10s + grace period za otvorena vrata
    - Ako je PIN tačan (1234) i alarm je aktivan → ugasi alarm i disarm sistem
    - Ako je PIN tačan (1234) i sistem je disarmed → arm za 10s + grace period
    - Ako je PIN netačan → ne radi ništa
    """
    def apply_grace_period():
        """Ako su DS1 ili DS2 otvoreni, postavi grace period da ne pale alarm."""
        for ds_key in ["DS1", "DS2"]:
            if system_state["ds_open_since"][ds_key] is not None:
                system_state["ds_grace_period"][ds_key] = True
                print(f"[PIN] Grace period aktiviran za {ds_key}")

    if entered_pin == ARM_PIN:
        apply_grace_period()
        if not system_state["is_system_armed"]:
            Timer(10, arm_system).start()
            print("🔒 Arm PIN (4321) — arming system in 10s")
        else:
            print("ℹ️ Arm PIN (4321) — system already armed")
        return

    if correct_pin(entered_pin):
        apply_grace_period()
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


# --- KITCHEN TIMER ---

timer_tick_ref = [None]  # mutable reference za Timer thread

def timer_tick():
    if not system_state["timer_running"]:
        return
    if system_state["timer_seconds"] <= 0:
        system_state["timer_running"] = False
        system_state["timer_expired"] = True
        system_state["timer_seconds"] = 0
        # Pošalji komandu 4SD da treperi sa 00:00
        mqtt_client.publish("commands/PI2/4SD", json.dumps({
            "display": "00:00",
            "blink": True
        }))
        print("[TIMER] Isteklo! 4SD treperi 00:00")
        return

    system_state["timer_seconds"] -= 1
    mins = system_state["timer_seconds"] // 60
    secs = system_state["timer_seconds"] % 60
    display_str = f"{mins:02d}:{secs:02d}"
    mqtt_client.publish("commands/PI2/4SD", json.dumps({
        "display": display_str,
        "blink": False
    }))

    # Zakaži sljedeći tick
    t = Timer(1.0, timer_tick)
    timer_tick_ref[0] = t
    t.start()


def start_timer(seconds):
    # Zaustavi prethodni tick ako postoji
    if timer_tick_ref[0] is not None:
        timer_tick_ref[0].cancel()

    system_state["timer_seconds"] = int(seconds)
    system_state["timer_initial"] = int(seconds)
    system_state["timer_running"] = True
    system_state["timer_expired"] = False
    system_state["timer_started_at"] = time.time()

    mins = system_state["timer_seconds"] // 60
    secs = system_state["timer_seconds"] % 60
    mqtt_client.publish("commands/PI2/4SD", json.dumps({
        "display": f"{mins:02d}:{secs:02d}",
        "blink": False
    }))

    t = Timer(1.0, timer_tick)
    timer_tick_ref[0] = t
    t.start()
    print(f"[TIMER] Start: {seconds}s")


def add_seconds_to_timer(n):
    system_state["timer_seconds"] += int(n)

    # Ako je bio expired, ponovo pokreni
    if system_state["timer_expired"]:
        system_state["timer_expired"] = False
        system_state["timer_running"] = True
        t = Timer(1.0, timer_tick)
        timer_tick_ref[0] = t
        t.start()
        print(f"[TIMER] BTN — treperenje zaustavljeno, nastavljam sa {system_state['timer_seconds']}s")
    else:
        print(f"[TIMER] BTN — dodato {n}s, ukupno: {system_state['timer_seconds']}s")

    mins = system_state["timer_seconds"] // 60
    secs = system_state["timer_seconds"] % 60
    mqtt_client.publish("commands/PI2/4SD", json.dumps({
        "display": f"{mins:02d}:{secs:02d}",
        "blink": False
    }))


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

        # Uključi DL
        system_state["last_dl"] = True
        mqtt_client.publish("commands/PI1/DL", json.dumps({"value": True}))
        print(f"[DPIR1] 💡 Motion → LED ON (10s)")

        # Ugasi DL nakon 10 sekundi
        def turn_off_dl():
            system_state["last_dl"] = False
            mqtt_client.publish("commands/PI1/DL", json.dumps({"value": False}))
            print("[DPIR1] 💡 LED auto-OFF after 10s")
        Timer(10, turn_off_dl).start()

        entered = handle_motion_event("pi1/dpir1", "DUS1")
        if entered is False and system_state["people_count"] == 0 and system_state["is_system_armed"]:
            activate_alarm(
                reason="Kretanje detektovano na izlazu, nema registrovanih osoba unutra",
                sensors=["DPIR1", "DUS1"]
            )

    elif topic == "pi2/dpir2" and value == 1:
        system_state["last_dpir"]["DPIR2"] = time.time()
        entered = handle_motion_event("pi2/dpir2", "DUS2")
        if entered is False and system_state["people_count"] == 0 and system_state["is_system_armed"]:
            activate_alarm(
                reason="Kretanje detektovano na izlazu (ulaz 2), nema registrovanih osoba unutra",
                sensors=["DPIR2", "DUS2"]
            )

    elif topic == "pi3/dpir3" and value == 1:
        system_state["last_dpir"]["DPIR3"] = time.time()
        if system_state["people_count"] == 0 and system_state["is_system_armed"]:
            activate_alarm(
                reason="Kretanje detektovano u dnevnoj sobi, nema registrovanih osoba unutra",
                sensors=["DPIR3"]
            )

    elif topic == "pi2/gsg":
        movement = data.get("movement")
        magnitude = data.get("value")
        system_state["last_gsg"] = magnitude
        if movement >= 1:
            print(f"[GSG] 🚰 Faucet movement detected! Magnitude: {magnitude}g")
            activate_alarm(
                reason=f"Detektovano neobično kretanje slavine/gyroscopea (intenzitet: {magnitude}g)",
                sensors=["GSG"]
            )

    elif topic == "pi1/ds1":
        system_state["last_ds_readings"]["DS1"] = value
        if value == 1 or value is True:
            if system_state["ds_open_since"]["DS1"] is None:
                system_state["ds_open_since"]["DS1"] = time.time()
                print(f"[DS1] 🚪 Vrata otvorena — čekam {DOOR_OPEN_ALARM_DELAY}s...")
                Timer(DOOR_OPEN_ALARM_DELAY, lambda: check_ds_alarm("DS1")).start()
        else:
            system_state["ds_open_since"]["DS1"] = None
            system_state["ds_grace_period"]["DS1"] = False
            if system_state["ds_alarm_active"]["DS1"]:
                system_state["ds_alarm_active"]["DS1"] = False
                # Ukloni DS1 iz aktivnih triggera
                system_state["alarm_triggers"] = [t for t in system_state["alarm_triggers"] if t != "DS1"]
                print("[DS1] 🚪 Vrata zatvorena — DS1 uklonjen iz alarma")
                if not any_ds_alarm_active():
                    deactivate_alarm()
                else:
                    # Drugi DS još aktivan — ažuriraj reason
                    remaining = [t for t in system_state["alarm_triggers"] if t.startswith("DS")]
                    system_state["alarm_reason"] = f"Vrata {', '.join(remaining)} još uvijek otvorena"
                    print(f"[DS1] Alarm ostaje aktivan zbog: {remaining}")

    elif topic == "pi2/ds2":
        system_state["last_ds_readings"]["DS2"] = value
        if value == 1:
            if system_state["ds_open_since"]["DS2"] is None:
                system_state["ds_open_since"]["DS2"] = time.time()
                print(f"[DS2] 🚪 Vrata otvorena — čekam {DOOR_OPEN_ALARM_DELAY}s...")
                Timer(DOOR_OPEN_ALARM_DELAY, lambda: check_ds_alarm("DS2")).start()
        else:
            system_state["ds_open_since"]["DS2"] = None
            system_state["ds_grace_period"]["DS2"] = False
            if system_state["ds_alarm_active"]["DS2"]:
                system_state["ds_alarm_active"]["DS2"] = False
                # Ukloni DS2 iz aktivnih triggera
                system_state["alarm_triggers"] = [t for t in system_state["alarm_triggers"] if t != "DS2"]
                print("[DS2] 🚪 Vrata zatvorena — DS2 uklonjen iz alarma")
                if not any_ds_alarm_active():
                    deactivate_alarm()
                else:
                    # Drugi DS još aktivan — ažuriraj reason
                    remaining = [t for t in system_state["alarm_triggers"] if t.startswith("DS")]
                    system_state["alarm_reason"] = f"Vrata {', '.join(remaining)} još uvijek otvorena"
                    print(f"[DS2] Alarm ostaje aktivan zbog: {remaining}")

    elif topic == "pi1/dl":
        system_state["last_dl"] = bool(value)

    elif topic == "pi2/btn":
        # Fizičko dugme u kuhinji — dodaj N sekundi na štopericu
        if value == 1:
            n = system_state["timer_btn_increment"]
            add_seconds_to_timer(n)
            print(f"[BTN] Pritisnuto — +{n}s na štopericu")

    elif topic == "timer/set":
        seconds = data.get("seconds")
        if seconds is not None:
            start_timer(seconds)

    elif topic == "timer/increment":
        increment = data.get("increment")
        if increment is not None:
            system_state["timer_btn_increment"] = int(increment)
            print(f"[TIMER] BTN inkrement postavljen na {increment}s")

    elif topic == "pi1/dms":
        system_state["entered_pin"] += str(value)
        if len(system_state["entered_pin"]) == 4:
            manage_alarm_system(system_state["entered_pin"])
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
        ir_commands = {
            "0x300ff22dd": "off",
            "0x300ffc23d": "red",
            "0x300ff629d": "green",
            "0x300ffa857": "blue",
            "0x300ff9867": "white",
            "0x300ffb04f": "yellow",
            "0x300ff02fd": "purple",
            "0x300ffc23f": "light blue"
        }

        target_color = ir_commands.get(value, "off")

        system_state["last_ir"] = value
        print(system_state["last_ir"])
        mqtt_client.publish("commands/PI3/BRGB", json.dumps({"color": target_color}))

        print(f"[PI3] IR Komanda: {value} -> Boja: {target_color}")


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

@app.route('/simulate/sensor', methods=['POST'])
def simulate_sensor():
    content = request.json
    scenario = content.get('scenario')

    if scenario == "1":
        payload = json.dumps({
            "measurement": "pi1/dpir1",
            "value": 1,
            "simulated": True,
            "runs_on": "flask",
            "name": "DPIR1"
        })
        mqtt_client.publish("pi1/dpir1", payload, qos=1)
        return jsonify({"status": "success", "message": "Scenarij 1: DPIR1 simuliran — LED će se upaliti na 10s"})

    elif scenario == "2a":
        # FIX: očisti staru DUS historiju prije simulacije da nema lažnih podataka
        system_state["dus_history"]["DUS1"] = []

        mqtt_client.publish("pi1/dus1", json.dumps({
            "measurement": "pi1/dus1", "value": 30.0,
            "simulated": True, "runs_on": "flask", "name": "DUS1"
        }), qos=1)

        def trigger():
            # FIX: debug log da vidimo stanje historije u trenutku okidanja
            hist = system_state["dus_history"]["DUS1"]
            cooldown_elapsed = time.time() - system_state["last_motion_event"]["DUS1"]
            print(f"[2a DEBUG] DUS1 history ({len(hist)} entries): {hist}")
            print(f"[2a DEBUG] Cooldown elapsed: {cooldown_elapsed:.2f}s (limit: {MOTION_COOLDOWN}s)")
            mqtt_client.publish("pi1/dpir1", json.dumps({
                "measurement": "pi1/dpir1", "value": 1,
                "simulated": True, "runs_on": "flask", "name": "DPIR1"
            }), qos=1)

        # FIX: delay povećan sa 0.5s → 1.0s da DUS sigurno stigne u historiju
        Timer(1.0, trigger).start()
        return jsonify({
            "status": "success",
            "message": f"Scenarij 2a: osoba ULAZI | trenutno: {system_state['people_count']} osoba"
        })

    elif scenario == "2b":
        # FIX: očisti staru DUS historiju prije simulacije
        system_state["dus_history"]["DUS1"] = []

        mqtt_client.publish("pi1/dus1", json.dumps({
            "measurement": "pi1/dus1", "value": 120.0,
            "simulated": True, "runs_on": "flask", "name": "DUS1"
        }), qos=1)

        def trigger():
            hist = system_state["dus_history"]["DUS1"]
            cooldown_elapsed = time.time() - system_state["last_motion_event"]["DUS1"]
            print(f"[2b DEBUG] DUS1 history ({len(hist)} entries): {hist}")
            print(f"[2b DEBUG] Cooldown elapsed: {cooldown_elapsed:.2f}s (limit: {MOTION_COOLDOWN}s)")
            mqtt_client.publish("pi1/dpir1", json.dumps({
                "measurement": "pi1/dpir1", "value": 1,
                "simulated": True, "runs_on": "flask", "name": "DPIR1"
            }), qos=1)

        # FIX: delay povećan sa 0.5s → 1.0s
        Timer(1.0, trigger).start()
        return jsonify({
            "status": "success",
            "message": f"Scenarij 2b: osoba IZLAZI | trenutno: {system_state['people_count']} osoba"
        })

    elif scenario == "3":
        mqtt_client.publish("pi1/ds1", json.dumps({
            "measurement": "pi1/ds1",
            "value": 1,
            "simulated": True,
            "runs_on": "flask",
            "name": "DS1"
        }), qos=1)
        return jsonify({
            "status": "success",
            "message": "Scenarij 3: DS1 otvoren — alarm aktivira se za 5s ako vrata ostanu otvorena"
        })

    elif scenario == "5":
        current_people = system_state.get('people_count', 0)
        dpirs_sensors = [
            {"topic": "pi1/dpir1", "name": "DPIR1"},
            {"topic": "pi2/dpir2", "name": "DPIR2"},
            {"topic": "pi3/dpir3", "name": "DPIR3"}
        ]

        chosen_sensor = random.choice(dpirs_sensors)
        print(f"Chosen sensor: {chosen_sensor}")
        payload = json.dumps({
            "measurement": chosen_sensor["topic"],
            "value": 1,
            "simulated": True,
            "runs_on": "flask",
            "name": chosen_sensor["name"]
        })

        mqtt_client.publish(chosen_sensor["topic"], payload, qos=1)

        if current_people == 0:
            return jsonify({
                "status": "success",
                "message": f"Scenarij 5: Pokret na {chosen_sensor['name']} detektovan. Objekt je prazan -> ALARM!"
            })
        else:
            return jsonify({
                "status": "success",
                "message": f"Scenarij 5: Pokret na {chosen_sensor['name']} detektovan, ali ima {current_people} osoba. Nema alarma."
            })

    elif scenario == "6":
        magnitude = 2.5
        mqtt_client.publish("pi2/gsg", json.dumps({
            "measurement": "pi2/gsg",
            "value": magnitude,
            "movement": 1,
            "simulated": True,
            "runs_on": "flask",
            "name": "GSG"
        }), qos=1)
        return jsonify({
            "status": "success",
            "message": f"Scenarij 6: GSG pomeraj detektovan ({magnitude}g) — alarm aktiviran"
        })

    elif scenario == "9":
        colors = [
            {"command": "0x300ff22dd", "value": "off"},
            {"command": "0x300ffc23d", "value": "red"},
            {"command": "0x300ff629d", "value": "green"},
            {"command": "0x300ffa857", "value": "blue"},
            {"command": "0x300ff9867", "value": "white"},
            {"command": "0x300ffb04f", "value": "yellow"},
            {"command": "0x300ff02fd", "value": "purple"},
            {"command": "0x300ffc23f", "value": "light blue"}
        ]

        color = random.choice(colors)
        payload = json.dumps({
            "measurement": "pi3/ir",
            "simulated": True,
            "runs_on": "flask",
            "name": "IR",
            "value": color["command"]
        })

        mqtt_client.publish("pi3/ir", payload, qos=1)
        return jsonify({
            "status": "success",
            "message": f"Scenarij 9: Primljena je komanda {color['command']} — boja: {color['value']} "
        })

    return jsonify({"status": "error", "message": "Nepoznat scenarij"}), 400


@app.route('/system/state', methods=['GET'])
def get_system_state():
    return jsonify({
        "status": "success",
        "data": {
            "people_count": system_state["people_count"],
            "is_alarm_active": system_state["is_alarm_active"],
            "is_system_armed": system_state["is_system_armed"],
            "alarm_reason": system_state["alarm_reason"],
            "alarm_triggers": system_state["alarm_triggers"],
            "alarm_activated_at": system_state["alarm_activated_at"],
        }
    })


@app.route('/system/sensors', methods=['GET'])
def get_sensors():
    now = time.time()
    dpir1_active = (now - system_state["last_dpir"]["DPIR1"]) < 2 if system_state["last_dpir"]["DPIR1"] else False
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
    is_arm_pin = pin == ARM_PIN

    return jsonify({
        "status": "success",
        "message": "PIN prihvaćen — alarm deaktiviran" if (is_correct and not system_state["is_alarm_active"]) else
                   "ARM PIN prihvaćen — sistem se naoružava za 10s" if is_arm_pin else
                   "PIN prihvaćen — sistem se naoružava za 10s" if (is_correct and not system_state["is_system_armed"]) else
                   "PIN prihvaćen" if is_correct else
                   "Pogrešan PIN",
        "correct": is_correct or is_arm_pin,
        "alarm_active": system_state["is_alarm_active"],
        "system_armed": system_state["is_system_armed"],
    })


@app.route('/rgb/set', methods=['POST'])
def set_rgb():
    content = request.json
    print(content)
    color = content.get('color')
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
        start_timer(int(seconds))
        mqtt_client.publish("timer/set", json.dumps({"seconds": int(seconds)}), qos=1)
        return jsonify({"status": "success", "message": f"Štoperica postavljena na {seconds}s"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/timer/increment', methods=['POST'])
def set_timer_increment():
    content = request.json
    increment = content.get('increment')
    if increment is None:
        return jsonify({"status": "error", "message": "No increment provided"}), 400
    try:
        system_state["timer_btn_increment"] = int(increment)
        mqtt_client.publish("timer/increment", json.dumps({"increment": int(increment)}), qos=1)
        return jsonify({"status": "success", "message": f"BTN inkrement postavljen na {increment}s"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/timer/state', methods=['GET'])
def get_timer_state():
    return jsonify({
        "status": "success",
        "data": {
            "seconds": system_state["timer_seconds"],
            "initial": system_state["timer_initial"],
            "running": system_state["timer_running"],
            "expired": system_state["timer_expired"],
            "btn_increment": system_state["timer_btn_increment"],
        }
    })


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