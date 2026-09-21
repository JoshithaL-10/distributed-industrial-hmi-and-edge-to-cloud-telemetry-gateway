import time
import json
import struct
import random
import paho.mqtt.client as mqtt

# --- Configuration ---
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC_TELEMETRY = "master_project/industrial_hmi/telemetry"
TOPIC_ALERTS = "master_project/industrial_hmi/alerts"

def calculate_checksum(data: bytes) -> int:
    cs = 0
    for b in data:
        cs ^= b
    return cs

def simulate_psoc_capsense_frame(tick: int) -> bytes:
    """Simulate Infineon PSoC 4100T MSCLP Sensing Engine"""
    status = 0x00
    x, y = 0, 0
    als_lux = int(350 + 50 * random.random())
    
    # Simulate states: Idle -> Approach (Proximity) -> Touch -> Splash Noise
    phase = tick % 20
    if phase == 5:
        status |= 0x01  # Proximity active
    elif phase in [6, 7]:
        status |= 0x01 | 0x08  # Proximity + Touchpad Contact
        x = 50 + (phase - 6) * 20
        y = 30 + (phase - 6) * 10
    elif phase == 12:
        status |= 0x02  # Button 0 Pressed (Cleanroom/Terminal Acknowledge)
    elif phase == 16:
        # Simulate water droplet noise trigger
        status |= 0x08
        x = 99
        y = 99

    payload = struct.pack("<BBHH", status, x, y, als_lux)
    checksum = calculate_checksum(payload)
    return payload + struct.pack("<B", checksum)

def parse_and_process_ra0e3_fsm(frame: bytes):
    """Simulate Renesas RA0E3 Deterministic Safety Host Controller"""
    if len(frame) != 7:
        return None, "FRAME_ERR_LENGTH"
    
    payload = frame[:6]
    received_checksum = frame[6]
    
    if calculate_checksum(payload) != received_checksum:
        return None, "CHECKSUM_MISMATCH"
    
    status, x, y, als = struct.unpack("<BBHH", payload)
    
    # State validation
    proximity = bool(status & 0x01)
    btn0 = bool(status & 0x02)
    touch_active = bool(status & 0x08)
    
    # Water rejection filter logic
    if touch_active and x > 95 and y > 95:
        event = "WATER_DROPLET_REJECTED"
        access_state = "IDLE_PROTECTED"
    elif btn0:
        event = "ACCESS_REQUEST_CONFIRMED"
        access_state = "AUTHORIZED_UNLOCK"
    elif touch_active:
        event = f"TOUCHPAD_COORDINATE_INPUT: ({x}, {y})"
        access_state = "VERIFYING_PIN"
    elif proximity:
        event = "USER_PROXIMITY_DETECTED"
        access_state = "WAKE_ON_TOUCH_READY"
    else:
        event = "STANDBY"
        access_state = "DEEP_SLEEP_SECURE"
        
    packet = {
        "device": "RENESAS_RA0E3_HOST",
        "coprocessor": "INFINEON_PSOC4100T",
        "access_state": access_state,
        "event": event,
        "metrics": {
            "proximity": proximity,
            "btn0": btn0,
            "touchpad_active": touch_active,
            "x": x,
            "y": y,
            "als_lux": als
        },
        "bus_integrity": "OK"
    }
    return packet, None

def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    print(f"[*] Connecting to public MQTT broker: {BROKER}:{PORT}...")
    try:
        client.connect(BROKER, PORT, keepalive=60)
        client.loop_start()
        print("[+] MQTT connected successfully!")
        print(f"[*] Publishing to Topic: {TOPIC_TELEMETRY}")
        print("[*] Web dashboard: http://www.hivemq.com/demos/websocket-client/\n")
    except Exception as e:
        print(f"[-] Broker connection failed: {e}")
        return

    tick = 0
    try:
        while True:
            # 1. PSoC generates sensor frame
            raw_frame = simulate_psoc_capsense_frame(tick)
            
            # 2. Renesas RA0E3 parses frame & enforces access state machine
            telemetry, err = parse_and_process_ra0e3_fsm(raw_frame)
            
            if err:
                alert = {"device": "RA0E3", "alert": err, "timestamp": time.time()}
                client.publish(TOPIC_ALERTS, json.dumps(alert))
                print(f"[!] SYSTEM FAULT: {err}")
            else:
                json_str = json.dumps(telemetry)
                client.publish(TOPIC_TELEMETRY, json_str)
                print(f"[TX Cloud] State: {telemetry['access_state']:<22} | Event: {telemetry['event']}")
            
            tick += 1
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\n[*] Stopping simulation...")
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()