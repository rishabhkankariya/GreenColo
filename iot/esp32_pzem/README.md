# ESP32 + PZEM-004T Hardware Integration Guide

This directory contains the Arduino C++ firmware for the **GreenColo** physical energy monitoring bench.

---

## 1. Hardware Required

1. **ESP32 NodeMCU / DevKit v1** (Wi-Fi enabled microcontroller)
2. **PZEM-004T v3.0** AC Energy Meter module (with split-core Current Transformer / CT clamp)
3. **5V USB Power Supply** (for ESP32 and PZEM logic)
4. **Controlled Electrical Test Load** (e.g. laptop power brick, lab PC, or small heater/lamp)
5. **Insulated Junction Box** for electrical safety

---

## 2. Wiring Connections

### A. Low-Voltage Logic Connections (DC Side - SAFE)

| PZEM-004T Pin | ESP32 Pin | Note |
| :--- | :--- | :--- |
| **5V** | **VIN / 5V** | Power for PZEM logic circuit |
| **GND** | **GND** | Common ground |
| **TX** | **GPIO 16 (RX2)** | PZEM Transmit $\rightarrow$ ESP32 Receive |
| **RX** | **GPIO 17 (TX2)** | PZEM Receive $\rightarrow$ ESP32 Transmit |

> **Note:** The PZEM-004T has an integrated optocoupler isolating the high-voltage mains side from the low-voltage TTL serial pins.

### B. High-Voltage Connections (AC Mains Side - CAUTION)

- Connect AC **Live (L)** and **Neutral (N)** screw terminals to the 230V AC supply.
- Clamp the split-core Current Transformer (**CT**) around **ONLY ONE** wire (either Live or Neutral, **NOT both**).

---

## 3. Flashing Firmware via Arduino IDE

1. Open Arduino IDE.
2. Go to **Sketch** $\rightarrow$ **Include Library** $\rightarrow$ **Manage Libraries...** and install:
   - `PZEM004Tv30` by Mandar Joshi
   - `ArduinoJson` (v6.x or v7.x) by Benoît Blanchon
3. Select Board: **ESP32 Dev Module**.
4. In `esp32_pzem.ino`:
   - Replace `WIFI_SSID` and `WIFI_PASSWORD` with your local Wi-Fi credentials.
   - Replace `BACKEND_URL` with your computer's local IP address (e.g., `http://192.168.1.100:8000/api/v1/telemetry/power`).
5. Select COM port and click **Upload**.
6. Open **Serial Monitor** at **115200 baud** to verify readings.
