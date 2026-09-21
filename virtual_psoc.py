import socket
import struct
import time
import random
import sys

HOST = "127.0.0.1"
PORT = 5000

class VirtualCapSenseEngine:
    def __init__(self):
        self.baseline_noise = 12.0

    def generate_packet(self, mode="normal"):
        event_status = 0
        x = 0
        y = 0

        if mode == "proximity":
            event_status = 0x01
        elif mode == "button0":
            event_status = 0x02
        elif mode == "button1":
            event_status = 0x04
        elif mode == "touchpad":
            event_status = 0x08
            x = random.randint(15, 85)
            y = random.randint(20, 80)
        elif mode == "water_noise":
            event_status = 0x08
            x = random.randint(1, 8)
            y = random.randint(1, 8)

        lux = random.randint(450, 520)
        als_msb = (lux >> 8) & 0xFF
        als_lsb = lux & 0xFF

        checksum = event_status ^ x ^ y ^ als_msb ^ als_lsb

        if mode == "corrupt":
            checksum ^= 0xFF  # Invalidate checksum for negative testing

        packet = struct.pack("BBBBBB", event_status, x, y, als_msb, als_lsb, checksum)
        return packet, lux, event_status

def run_server():
    engine = VirtualCapSenseEngine()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind((HOST, PORT))
    except socket.error as e:
        print(f"[Error] Failed to bind to {HOST}:{PORT}: {e}")
        sys.exit(1)

    server.listen(1)
    print("===================================================================")
    print(f" [PSoC 4100T Virtual Sensor] Listening on {HOST}:{PORT} (I2C Emulation)")
    print("===================================================================")
    print("Waiting for Renesas RA0E3 Host Controller to connect...\n")

    conn, addr = server.accept()
    print(f"[PSoC 4100T] Host Controller connected from {addr}\n")

    modes = ["proximity", "touchpad", "button0", "button1", "corrupt", "touchpad"]

    try:
        for idx, mode in enumerate(modes, start=1):
            packet, lux, status = engine.generate_packet(mode=mode)
            conn.sendall(packet)

            status_desc = {
                0x01: "PROXIMITY_ALERT",
                0x02: "BUTTON_0_PRESS",
                0x04: "BUTTON_1_PRESS",
                0x08: "TOUCHPAD_COORDINATES",
                0x00: "IDLE / NOISE"
            }.get(status, "UNKNOWN")

            print(f"[Step {idx:02d}] Injected Event Mode: {mode.upper()}")
            print(f"          Status: 0x{status:02X} ({status_desc}) | ALS: {lux} Lux")
            print(f"          Raw I2C Bytes Sent: {[hex(b) for b in packet]}\n")
            time.sleep(2)
    except (BrokenPipeError, ConnectionResetError):
        print("[PSoC 4100T] Host Controller disconnected.")
    finally:
        conn.close()
        server.close()
        print("[PSoC 4100T] Virtual sensor simulation terminated.")

if __name__ == "__main__":
    run_server()