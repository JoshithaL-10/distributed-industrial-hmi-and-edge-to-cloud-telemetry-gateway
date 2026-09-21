import json
import paho.mqtt.client as mqtt

BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC_TELEMETRY = "master_project/industrial_hmi/telemetry"
TOPIC_COMMANDS = "master_project/industrial_hmi/commands"

def on_connect(client, userdata, flags, rc, properties=None):
    print("\n==================================================")
    print(" [ESP32 Gateway Node] Booted & Online")
    print(f" [Subscribed] 1. {TOPIC_TELEMETRY}")
    print(f" [Subscribed] 2. {TOPIC_COMMANDS}")
    print("==================================================\n")
    # Subscribe to both channels
    client.subscribe([(TOPIC_TELEMETRY, 0), (TOPIC_COMMANDS, 0)])

def on_message(client, userdata, msg):
    try:
        # Route 1: Downstream Emergency Cloud Command
        if msg.topic == TOPIC_COMMANDS:
            cmd = json.loads(msg.payload.decode())
            print("\n" + "!" * 55)
            print(f" [DOWNSTREAM COMMAND] Action: {cmd.get('command')}")
            print(f"                      Source: {cmd.get('authorized_by')}")
            print(" [UART -> RA0E3 HOST] Interlock Triggered: SYSTEM LOCKED")
            print("!" * 55 + "\n")
            return

        # Route 2: Upstream Sensor Telemetry
        payload = json.loads(msg.payload.decode())
        state = payload.get("access_state", "UNKNOWN")
        event = payload.get("event", "NO_EVENT")
        metrics = payload.get("metrics", {})
        print(f"[ESP32 RX] State: {state:<22} | Event: {event}")
        print(f"           --> GPIO2 (LED): BLINK | Ambient: {metrics.get('als_lux')} lux")
        
    except Exception as e:
        print(f"[ESP32 ERR] Parse error: {e}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

print("[ESP32] Initializing Wi-Fi stack & connecting to broker...")
client.connect(BROKER, PORT, 60)
client.loop_forever()