import socket
import struct
import time

SERVER_IP = "127.0.0.1"
SERVER_PORT = 5000
MASTER_PIN = 12

def validate_checksum(data: bytes) -> bool:
    # Parity check: XOR across bytes 0 to 4 must equal byte 5
    chk = 0
    for b in data[:5]:
        chk ^= b
    return chk == data[5]

def main():
    print("===================================================================")
    print("  [Renesas RA0E3 Host Controller] Initializing SIL FSM Engine...")
    print("===================================================================\n")

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(f"[RA0E3 Host] Connecting to PSoC 4100T Virtual I2C bus at {SERVER_IP}:{SERVER_PORT}...")

    while True:
        try:
            s.connect((SERVER_IP, SERVER_PORT))
            break
        except ConnectionRefusedError:
            print("[RA0E3 Host] Waiting for virtual sensor server to come online...")
            time.sleep(1)

    print("[RA0E3 Host] I2C Bus Link Active. Listening for sensor events...\n")

    state = "LOCKED"
    entered_pin = 0

    while True:
        data = s.recv(6)
        if not data:
            print("[RA0E3 Host] Virtual I2C bus closed. Exiting.")
            break

        if len(data) == 6:
            status, x, y, msb, lsb, chk = struct.unpack("BBBBBB", data)
            lux = (msb << 8) | lsb

            if validate_checksum(data):
                # Deterministic Security State Machine
                if state == "LOCKED" and (status & 0x01):
                    state = "PIN_ENTRY_MODE"
                elif state == "PIN_ENTRY_MODE":
                    if status & 0x02:
                        entered_pin = (entered_pin * 10) + 1
                        state = "DIGIT_1_RECORDED"
                    elif status & 0x04:
                        entered_pin = (entered_pin * 10) + 2
                        state = "DIGIT_2_RECORDED"
                    elif status & 0x08:
                        if entered_pin == MASTER_PIN:
                            state = "ACCESS_GRANTED_UNLOCKED"
                        else:
                            state = "AUTH_FAILED_LOCKED"
                            entered_pin = 0

                print(f"[I2C Read PASS] Checksum Verified: 0x{chk:02X}")
                print(f"                -> Host State: {state:<24} | Lux: {lux} | Coords: ({x}, {y})\n")
            else:
                print(f"[I2C Read FAIL] Checksum mismatch! Corrupted packet rejected (0x{chk:02X})\n")

    s.close()

if __name__ == "__main__":
    main()