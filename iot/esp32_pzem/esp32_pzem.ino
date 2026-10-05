/*
 * GreenColo: ESP32 + PZEM-004T Power Telemetry Firmware
 * Target Hardware: ESP32 DevKit v1 + PZEM-004T v3.0 (AC Energy Meter)
 * 
 * Function:
 *   - Reads Voltage (V), Current (A), Power (W), Energy (kWh), Frequency (Hz), and Power Factor
 *   - Formats a JSON payload matching the GreenColo FastAPI contract
 *   - Sends an HTTP POST request to /api/v1/telemetry/power every POLL_INTERVAL_MS
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>      // Install ArduinoJson v6.x or v7.x
#include <PZEM004Tv30.h>      // Install PZEM004Tv30 by Mandar Joshi

// -------------------------------------------------------------
// Configuration (Replace with your local network settings)
// -------------------------------------------------------------
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// GreenColo Ingestion Endpoint
// (Use your computer's local IP address if running backend locally, e.g., http://192.168.1.100:8000/api/v1/telemetry/power)
const char* BACKEND_URL   = "http://192.168.1.100:8000/api/v1/telemetry/power";
const char* DEVICE_ID     = "pzem_bench_01";

// Pinout for ESP32 HardwareSerial2
// PZEM TX -> ESP32 RX2 (GPIO 16)
// PZEM RX -> ESP32 TX2 (GPIO 17)
#define PZEM_RX_PIN 16
#define PZEM_TX_PIN 17

#define POLL_INTERVAL_MS 2000

// Initialize PZEM on Serial2
PZEM004Tv30 pzem(Serial2, PZEM_RX_PIN, PZEM_TX_PIN);

unsigned long lastPollTime = 0;

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n[GreenColo] Initializing ESP32 Power Monitor...");

  // Connect to Wi-Fi
  Serial.print("[WiFi] Connecting to: ");
  Serial.println(WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\n[WiFi] Connected!");
  Serial.print("[WiFi] IP Address: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  unsigned long now = millis();
  if (now - lastPollTime >= POLL_INTERVAL_MS) {
    lastPollTime = now;

    // Read PZEM sensor metrics
    float voltage   = pzem.voltage();
    float current   = pzem.current();
    float power     = pzem.power();
    float energy    = pzem.energy();
    float frequency = pzem.frequency();
    float pf        = pzem.pf();

    // Check if readings are valid
    if (isnan(voltage) || isnan(current) || isnan(power)) {
      Serial.println("[PZEM] Error reading sensor! Check wiring and AC power.");
      return;
    }

    Serial.printf("[PZEM] V: %.1fV | I: %.2fA | P: %.1fW | E: %.3fkWh | PF: %.2f\n",
                  voltage, current, power, energy, pf);

    // Only attempt transmission if WiFi is connected
    if (WiFi.status() == WL_CONNECTED) {
      HTTPClient http;
      http.begin(BACKEND_URL);
      http.addHeader("Content-Type", "application/json");

      // Construct JSON payload matching the FastAPI schema
      StaticJsonDocument<256> doc;
      doc["device_id"]    = DEVICE_ID;
      doc["source"]       = "pzem-004t";
      doc["voltage_v"]    = voltage;
      doc["current_a"]    = current;
      doc["power_w"]      = power;
      doc["energy_kwh"]   = energy;
      doc["power_factor"] = pf;
      doc["frequency_hz"] = frequency;

      String requestBody;
      serializeJson(doc, requestBody);

      int httpResponseCode = http.POST(requestBody);

      if (httpResponseCode > 0) {
        Serial.printf("[HTTP] POST Result: %d\n", httpResponseCode);
      } else {
        Serial.printf("[HTTP] POST Failed, error: %s\n", http.errorToString(httpResponseCode).c_str());
      }

      http.end();
    } else {
      Serial.println("[WiFi] Disconnected! Reconnecting...");
      WiFi.reconnect();
    }
  }
}
