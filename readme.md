# Distributed Industrial HMI & Edge-to-Cloud Telemetry Gateway
### Heterogeneous Multi-MCU Architecture: Infineon PSoC 4100T + Renesas RA0E3 + ESP32

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Arm%20Cortex--M0%2B%20%7C%20Cortex--M23%20%7C%20Xtensa-orange)](https://github.com)
[![Validation](https://img.shields.io/badge/Validation-Software--in--the--Loop%20(SIL)-green)](https://github.com)
[![IoT Broker](https://img.shields.io/badge/Telemetry-MQTT%20Over%20WebSockets-purple)](https://www.hivemq.com)

A robust, contactless Human-Machine Interface (HMI) and access telemetry system designed for harsh industrial, sterile cleanroom, and high-pressure washdown environments. The architecture partitions analog touch acquisition, deterministic safety logic, and cloud networking across three dedicated microcontrollers.

---

## 1. Problem Statement & Motivation

In sterile facilities (pharmaceutical isolators, semiconductor cleanrooms, and food processing lines), mechanical pushbuttons create crevices that harbor bio-burden, while consumer capacitive touchscreens generate continuous false actuations when sprayed with water or detergents. Furthermore, running Wi-Fi network stacks on a safety controller introduces latency that can block emergency interlocks.

This system resolves these vulnerabilities through a three-tier heterogeneous architecture:
* **Tier 1: Sensing Front-End (Infineon PSoC 4100T Plus):** Hardware-accelerated 5th-Gen MSCLP CapSense processing, mutual-capacitance matrix scanning, water-droplet noise filtering, and ambient light sensing (ALS).
* **Tier 2: Host Controller Brain (Renesas RA0E3 - Arm Cortex-M23):** Deterministic access control state machine, longitudinal XOR parity verification, and interlock control.
* **Tier 3: Cloud Messenger (ESP32):** Non-blocking FreeRTOS networking, JSON telemetry serialization, and bidirectional MQTT cloud communication.

```text
+-----------------------------------------------------------------------------------+
|                                INDUSTRIAL PERIMETER                               |
|                                                                                   |
|   +---------------------+    I2C Bus (400 kHz)    +---------------------------+   |
|   | Infineon PSoC 4100T | ----------------------> | Renesas RA0E3 (Host FSM)  |   |
|   | - 4x5 Matrix Touch  | <--- INT Pulse (P0.2) - | - Arm Cortex-M23 Core     |   |
|   | - Liquid Rejection  |                         | - Parity / Checksum Check |   |
|   | - Ambient Light ALS |                         | - Deterministic Safety    |   |
|   +---------------------+                         +---------------------------+   |
|                                                                 |                 |
|                                                        UART (115200 Baud)         |
|                                                                 v                 |
|                                                   +---------------------------+   |
|                                                   | ESP32 IoT Edge Gateway    |   |
|                                                   | - Non-blocking Wi-Fi      |   |
|                                                   | - MQTT Telemetry Stream   |   |
+---------------------------------------------------+-------------+-------------+---+
                                                                  |
                                                      MQTT / TLS (Port 8884/1883)
                                                                  v
                                                   +-----------------------------+
                                                   | Cloud Broker & Digital Twin |
                                                   | - HiveMQ Telemetry Stream   |
                                                   | - WebGL / Canvas Dashboard  |
                                                   +-----------------------------+
```

---

## 2. Inter-Chip Packet Protocol

Communication from the PSoC sensor front-end to the RA0E3 host uses a packed binary register frame protected by longitudinal XOR parity:

```text
Byte 0: Status Flags    -> Bit 0: Proximity | Bit 1: BTN0 | Bit 2: BTN1 | Bit 3: Touch Active
Byte 1: Touchpad X      -> Normalized coordinate (0 - 100)
Byte 2: Touchpad Y      -> Normalized coordinate (0 - 100)
Byte 3: Ambient Lux MSB -> High byte of 16-bit ALS reading
Byte 4: Ambient Lux LSB -> Low byte of 16-bit ALS reading
Byte 5: Checksum        -> Longitudinal XOR parity across Bytes 0 to 4
```

Frames with mismatched parity are rejected by the host controller before reaching the state machine.

---

## 3. Repository File Structure

```text
├── sil_orchestrator.py      # Full-stack simulation orchestrator publishing live MQTT data
├── esp32_gateway_node.py    # Virtual ESP32 node processing telemetry and lockdown commands
├── dashboard.html           # Live HTML5/Canvas UI rendering real-time 2D coordinates
├── virtual_psoc.py          # Standalone PSoC 4100T sensor server (I2C TCP emulation)
├── ra0e3_host_node.py       # Standalone RA0E3 host FSM verifying bus packets & state machine
├── ra0e3_fsm.c              # Native C implementation of RA0E3 Cortex-M23 host logic
└── README.md
```

---

## 4. How to Run the Software-in-the-Loop (SIL) Pipeline

### Pipeline 1: Cloud Digital Twin & Live Telemetry

1. **Install Python MQTT dependency:**
   ```bash
   pip install paho-mqtt
   ```

2. **Terminal 1 (Sensor & Safety Host Engine):**
   ```bash
   python sil_orchestrator.py
   ```

3. **Terminal 2 (Virtual ESP32 Gateway Node):**
   ```bash
   python esp32_gateway_node.py
   ```

4. **Launch the Live Dashboard:**
   * Open `dashboard.html` in any web browser to view the 4x5 coordinate canvas, system states, and lux levels in real time.

5. **Trigger Remote Lockdown (Cloud-to-Device Command):**
   * Using the HiveMQ Web Client, publish to topic: `master_project/industrial_hmi/commands`
   * Payload:
     ```json
     {"command": "FORCE_LOCKDOWN", "authorized_by": "ADMIN_OVERRIDE"}
     ```
   * The ESP32 node detects the command immediately and engages the local host interlock.

---

### Pipeline 2: Dual-Process Bus Emulation & Fault Injection

Tests direct inter-chip byte streaming over a virtual I2C link (TCP port 5000):

1. **Terminal 1 (PSoC Sensor Server):**
   ```bash
   python virtual_psoc.py
   ```

2. **Terminal 2 (RA0E3 Host Controller):**
   ```bash
   python ra0e3_host_node.py
   ```

Validates state transitions (`PIN_ENTRY_MODE` -> `ACCESS_GRANTED_UNLOCKED`) and verifies rejection of deliberately corrupted frames (`[I2C Read FAIL] Checksum mismatch! Corrupted packet rejected`).

---

## 5. Master's CV / Technical Portfolio Entry

* **Distributed Industrial HMI & Edge-to-Cloud Telemetry Gateway**
  * Engineered a three-tier heterogeneous embedded architecture isolating capacitive acquisition (Infineon PSoC 4100T), deterministic safety interlocks (Renesas RA0E3 Cortex-M23), and cloud networking (ESP32).
  * Implemented an inter-chip binary frame protocol with longitudinal XOR parity verification and liquid-droplet rejection algorithms.
  * Developed a Software-in-the-Loop (SIL) simulation framework in Python and native C to validate bus protocols, edge state machines, and MQTT cloud communication prior to hardware fabrication.
  * Built an interactive WebSocket-driven digital twin dashboard rendering 2D touch coordinates, ambient lux levels, and remote emergency lockdown commands in real time.
