# **Distributed Industrial HMI & Edge-to-Cloud Telemetry Gateway**

### **Heterogeneous Multi-MCU Architecture: Infineon PSoC 4100T \+ Renesas RA0E3 \+ ESP32**

A robust, contactless Human-Machine Interface (HMI) and access telemetry system designed for harsh industrial, sterile cleanroom, and high-pressure washdown environments. The architecture partitions analog touch acquisition, deterministic safety logic, and cloud networking across three dedicated microcontrollers.

## **1\. Problem Statement & Motivation**

In sterile facilities (pharmaceutical isolators, semiconductor cleanrooms, and food processing lines), mechanical pushbuttons create crevices that harbor bio-burden, while consumer capacitive touchscreens generate continuous false actuations when sprayed with water or detergents. Furthermore, running Wi-Fi network stacks on a safety controller introduces latency that can block emergency interlocks.

This system resolves these vulnerabilities through a three-tier heterogeneous architecture:

* **Tier 1: Sensing Front-End (Infineon PSoC 4100T Plus):** Hardware-accelerated 5th-Gen MSCLP CapSense processing, mutual-capacitance matrix scanning, water-droplet noise filtering, and ambient light sensing (ALS).  
* **Tier 2: Host Controller Brain (Renesas RA0E3 \- Arm Cortex-M23):** Deterministic access control state machine, longitudinal XOR parity verification, and interlock control.  
* **Tier 3: Cloud Messenger (ESP32):** Non-blocking FreeRTOS networking, JSON telemetry serialization, and bidirectional MQTT cloud communication.

\+-----------------------------------------------------------------------------------+  
|                                INDUSTRIAL PERIMETER                               |  
|                                                                                   |  
|   \+---------------------+    I2C Bus (400 kHz)    \+---------------------------+   |  
|   | Infineon PSoC 4100T | \----------------------\> | Renesas RA0E3 (Host FSM)  |   |  
|   | \- 4x5 Matrix Touch  | \<--- INT Pulse (P0.2) \- | \- Arm Cortex-M23 Core     |   |  
|   | \- Liquid Rejection  |                         | \- Parity / Checksum Check |   |  
|   | \- Ambient Light ALS |                         | \- Deterministic Safety    |   |  
|   \+---------------------+                         \+---------------------------+   |  
|                                                                 |                 |  
|                                                        UART (115200 Baud)         |  
|                                                                 v                 |  
|                                                   \+---------------------------+   |  
|                                                   | ESP32 IoT Edge Gateway    |   |  
|                                                   | \- Non-blocking Wi-Fi      |   |  
|                                                   | \- MQTT Telemetry Stream   |   |  
\+---------------------------------------------------+-------------+-------------+---+  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;MQTT / TLS (Port 8884/1883)  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;v  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\+-----------------------------+  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;| Cloud Broker & Digital Twin |  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;| \- HiveMQ Telemetry Stream   |  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;| \- WebGL / Canvas Dashboard  |  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\+-----------------------------+

## **2\. Inter-Chip Packet Protocol**

Communication from the PSoC sensor front-end to the RA0E3 host uses a packed binary register frame protected by longitudinal XOR parity:

Byte 0: Status Flags    \-\> Bit 0: Proximity | Bit 1: BTN0 | Bit 2: BTN1 | Bit 3: Touch Active  
Byte 1: Touchpad X      \-\> Normalized coordinate (0 \- 100\)  
Byte 2: Touchpad Y      \-\> Normalized coordinate (0 \- 100\)  
Byte 3: Ambient Lux MSB \-\> High byte of 16-bit ALS reading  
Byte 4: Ambient Lux LSB \-\> Low byte of 16-bit ALS reading  
Byte 5: Checksum        \-\> Longitudinal XOR parity across Bytes 0 to 4

Frames with mismatched parity are rejected by the host controller before reaching the state machine.

## **3\. Repository File Structure**

├── docs/  
│   ├── Screenshot 2026-09-21 170617.png    \# Live Coordinate Telemetry (70, 40\)  
│   ├── Screenshot 2026-09-21 170800.png    \# Verified Broker Stream (70, 40\)  
│   ├── Screenshot 2026-09-21 170821.png    \# Live Coordinate Telemetry (50, 30\)  
│   ├── Screenshot 2026-09-21 175053.png    \# Dual-Process Socket Initialization  
│   └── Screenshot 2026-09-21 175323.png    \# Injected Frame Corruption & Rejection  
├── sil\_orchestrator.py      \# Full-stack simulation orchestrator publishing live MQTT data  
├── esp32\_gateway\_node.py    \# Virtual ESP32 node processing telemetry and lockdown commands  
├── dashboard.html           \# Live HTML5/Canvas UI rendering real-time 2D coordinates  
├── virtual\_psoc.py          \# Standalone PSoC 4100T sensor server (I2C TCP emulation)  
├── ra0e3\_host\_node.py       \# Standalone RA0E3 host FSM verifying bus packets & state machine  
├── ra0e3\_fsm.c              \# Native C implementation of RA0E3 Cortex-M23 host logic  
└── README.md

## **4\. How to Run the Software-in-the-Loop (SIL) Pipeline**

### **Pipeline 1: Cloud Digital Twin & Live Telemetry**

1. **Install Python MQTT dependency:**  
   pip install paho-mqtt

2. **Terminal 1 (Sensor & Safety Host Engine):**  
   python sil\_orchestrator.py

3. **Terminal 2 (Virtual ESP32 Gateway Node):**  
   python esp32\_gateway\_node.py

4. **Launch the Live Dashboard:**  
   * Open dashboard.html in any web browser to view the 4x5 coordinate canvas, system states, and lux levels in real time.

#### **Telemetry Verification: Coordinate (50, 30\)**

The PSoC engine detects touch input at X: 50, Y: 30\. The RA0E3 host verifies packet parity and transitions to VERIFYING\_PIN. The ESP32 node serializes this frame to HiveMQ, while the HTML5 canvas renders the capacitive centroid:

#### **Telemetry Verification: Coordinate (70, 40\) & Ambient ALS**

As the finger translates across the 4x5 mutual-capacitance matrix to X: 70, Y: 40, real-time phototransistor lux readings (361–392 Lux) and proximity detection flags stream continuously through the broker:

5. **Trigger Remote Lockdown (Cloud-to-Device Command):**  
   * Using the HiveMQ Web Client or dashboard, publish to topic: master\_project/industrial\_hmi/commands  
   * Payload:  
     {"command": "FORCE\_LOCKDOWN", "authorized\_by": "ADMIN\_OVERRIDE"}

   * The ESP32 node intercepts the command and actuates the local safety interlock: \[UART \-\> RA0E3 HOST\] Interlock Triggered: SYSTEM LOCKED.

### **Pipeline 2: Dual-Process Bus Emulation & Fault Injection**

Tests direct chip-to-chip binary register exchange across a simulated ![][image1] bus over TCP port 5000:

1. **Terminal 1 (PSoC Sensor Server):**  
   python virtual\_psoc.py

2. **Terminal 2 (RA0E3 Host Controller):**  
   python ra0e3\_host\_node.py

#### **Bus Handshake & Normal State Execution**

The Python sensor server listens on port 5000 (I2C Emulation). The RA0E3 host connects, processes valid register frames, and executes state machine steps (PIN\_ENTRY\_MODE, BUTTON\_0\_PRESS, BUTTON\_1\_PRESS):

#### **Fault Injection & Checksum Rejection Verification**

In **Step 05**, an EMI transient / bit-flip fault is deliberately injected on the simulated bus (Injected Event Mode: CORRUPT with raw checksum 0x24). The host controller catches the mismatch, halts state transitions, and discards the malformed packet:

\[I2C Read FAIL\] Checksum mismatch\! Corrupted packet rejected (0x24)

## **5\. Master's CV / Technical Portfolio Entry**

* **Distributed Industrial HMI & Edge-to-Cloud Telemetry Gateway**  
  * Engineered a three-tier heterogeneous embedded architecture isolating capacitive acquisition (Infineon PSoC 4100T), deterministic safety interlocks (Renesas RA0E3 Cortex-M23), and cloud networking (ESP32).  
  * Implemented an inter-chip binary frame protocol with longitudinal XOR parity verification and liquid-droplet rejection algorithms.  
  * Developed a Software-in-the-Loop (SIL) simulation framework in Python and native C to validate bus protocols, edge state machines, and MQTT cloud communication prior to hardware fabrication.  
  * Built an interactive WebSocket-driven digital twin dashboard rendering 2D touch coordinates, ambient lux levels, and remote emergency lockdown commands in real time.

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACMAAAAaCAYAAAA9rOU8AAACM0lEQVR4Xu2UPWhUQRSF35IEIyGRXZb93/dWEESCWKgEQmpRxC4gJIWFhSLpLKKNaK9NihT+kEosJGC6QJr0qcXKUiE2QTGNKeJ3zEycd/etuzEkIuyBw7y599zZs3NnJor+VyRJch0uxnG80Gg0Jmz+2ICJc5i446aDzN9gqJ4SHRdqtdpZDDzzc4zNw4uhphNardYwtdVyuVwK48VicZRhIIztg8VvUfSK8bmn5nDGSXxhjtwS8dO+NguFQmEM3Sd0u4zfGb/AOVIDjJPEVmHe1v2CzgHJaYSvtUCz2byrebVaTUIdsXHym3zmwniAHLU30XyFt/P5/CmfoPatSHwLvgyLMiGRzEQZP6aFWWwNPrQ5hyFqn6oeLtskf/gMtZ9dftbmU6jX6xcQfaNg2+aIz2mnImdSWiORRi35WKlUWjbnEe+dt42OLfKQW7fghknpnLyQGZE23CuVSuVQwCFvqlbtDeMWzsyCjbdBIreFqX66HVN8n9yOkVBD7WPiH6xJC1p1DZ638RS0bdoR92N/7qcBu1Kk9j1cijLO2oEhAzLSUz8N0N9QLS26bHN/BbXGmTnwv/Nm4i4PIflH8d4l6IzDtEigdgru9GBmNenyWKaudLcFs6BDq8PLwbxqcwF0I+dtsA0stOx2RQ/VCZvvBXoQXaueYOqkj+ub2AO4EurboGvmTFiuW20viH8/DT/4fifyvQnvkx6y+iOHdohbdQUDs4yXon9hoo8++ugjAz8BOq2TxW0x/doAAAAASUVORK5CYII=>