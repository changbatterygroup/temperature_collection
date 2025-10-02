#include <ESP8266WiFi.h>
#include <ArduinoOTA.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>
#include <ArduinoJson.h>
#include <SimpleSyslog.h>

#ifndef WIFI_SSID
  #error "WIFI_SSID is not defined."
#endif
#ifndef WIFI_PASS
  #error "WIFI_PASS is not defined."
#endif
#ifndef OTA_HOSTNAME
  #error "OTA_HOSTNAME is not defined."
#endif
#ifndef OTA_PASSWORD
  #error "OTA_PASSWORD is not defined."
#endif
#ifndef SERVER_IP
  #error "SERVER_IP is not defined. Please provide it in the Makefile."
#endif
#ifndef API_KEY
  #error "API_KEY is not defined. Please provide it in the Makefile."
#endif
#ifndef TOPIC
  #error "TOPIC is not defined. Please provide it in the Makefile."
#endif

const char* ssid = WIFI_SSID;
const char* password = WIFI_PASS;
const char* ota_hostname = OTA_HOSTNAME;
const char* ota_password = OTA_PASSWORD;

IPAddress server_ip;

SimpleSyslog syslog(ota_hostname, "ESP8266_Lab", SERVER_IP);

unsigned long previousMillis = 0;
const long interval = 10000;

void logMessage(const char *format, ...) {
  char buf[256];
  va_list args;
  va_start(args, format);
  vsnprintf(buf, sizeof(buf), format, args);
  va_end(args);

  Serial.print(buf);
  
  syslog.printf(FAC_USER, PRI_INFO, "%s", buf);
}


void sendDataToServer() {
  if (WiFi.status() != WL_CONNECTED) {
    logMessage("WiFi Disconnected. Cannot send data.");
    return;
  }

  WiFiClient client;
  HTTPClient http;

  String serverUrl = "http://" + server_ip.toString() + ":5000/log";
  
  logMessage("Connecting to server: %s\n", serverUrl.c_str());

  if (http.begin(client, serverUrl)) {
    http.addHeader("Content-Type", "application/json");
    http.addHeader("X-API-Key", API_KEY);

    StaticJsonDocument<256> doc;
    float simulated_temp = random(2000, 2500) / 100.0;
    doc["topic"] = TOPIC;
    doc["temperature"] = simulated_temp;
    doc["mac_address"] = WiFi.macAddress();

    String output;
    serializeJson(doc, output);
    logMessage("Sending payload: %s\n", output.c_str());

    int httpCode = http.POST(output);

    String payload = http.getString();
    
    payload.trim();
    payload.replace("\n", "");
    payload.replace("\r", "");

    logMessage("[HTTP] Code=%d  Response: %s\n", httpCode, payload.c_str());

    http.end();
  } else {
    logMessage("[HTTP] Unable to connect\n");
  }
}

void setup() {
  Serial.begin(115200);
  while (!Serial) { delay(10); }
  logMessage("\nBooting...");

  if (!server_ip.fromString(SERVER_IP)) {
      Serial.println("FATAL: Could not parse SERVER_IP address. Halting.");
      while (true) { delay(1000); }
  }

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  logMessage("Connecting to WiFi SSID: %s\n", ssid);
  while (WiFi.status() != WL_CONNECTED) {
      delay(500);
      logMessage(".");
  }

  logMessage("\nWiFi connected!\n");
  logMessage("Local IP Address: %s\n", WiFi.localIP().toString().c_str());
  logMessage("Server IP Address: %s\n", server_ip.toString().c_str());
  logMessage("------------------------------------\n");


  ArduinoOTA.setHostname(ota_hostname);
  ArduinoOTA.setPassword(ota_password);
  ArduinoOTA.onStart([]() { Serial.println("OTA Update: Start"); });
  ArduinoOTA.onEnd([]() { Serial.println("\nOTA Update: End"); });
  ArduinoOTA.onProgress([](unsigned int p, unsigned int t) { Serial.printf("OTA Progress: %u%%\r", (p / (t / 100))); });
  ArduinoOTA.onError([](ota_error_t error) { Serial.printf("OTA Error[%u]", error); });
  ArduinoOTA.begin();
  logMessage("OTA Ready. Hostname: %s\n", ota_hostname);
  logMessage("------------------------------------");
}

void loop() {
  ArduinoOTA.handle();

  unsigned long currentMillis = millis();

  if (currentMillis - previousMillis >= interval) {
      previousMillis = currentMillis;
      sendDataToServer();
  }
}