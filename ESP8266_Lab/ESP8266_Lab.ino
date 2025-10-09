#include <ESP8266WiFi.h>
#include <ArduinoOTA.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>
#include <ArduinoJson.h>
#include <SimpleSyslog.h>
#include <Adafruit_BME280.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>
#include <math.h>

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
  #error "SERVER_IP is not defined."
#endif
#ifndef API_KEY
  #error "API_KEY is not defined."
#endif
#ifndef TOPIC
  #error "TOPIC is not defined."
#endif

#define SEALEVELPRESSURE_HPA (1013.25)


const char* ssid = WIFI_SSID;
const char* password = WIFI_PASS;
const char* ota_hostname = OTA_HOSTNAME;
const char* ota_password = OTA_PASSWORD;

Adafruit_BME280 bme;

IPAddress server_ip;

SimpleSyslog syslog(ota_hostname, ota_hostname, SERVER_IP);

unsigned long previousMillis = 0;
const long INTERVAL = 30000; // 30 secs

int failedRequests = 0;
const int MAX_FAILED_REQUESTS = 5;

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
    WiFi.reconnect();
    return;
  }

  if(!bme.begin()) {
    logMessage("%s\n", "BME sensor not found. Check wiring.");
    failedRequests++;
    return;
  }

  WiFiClient client;
  HTTPClient http;

  String serverUrl = "http://" + server_ip.toString() + ":5000/log";

  if (http.begin(client, serverUrl)) {
    http.addHeader("Content-Type", "application/json");
    http.setTimeout(5000);
    http.addHeader("X-API-Key", API_KEY);

    StaticJsonDocument<256> doc;

    float tempC = bme.readTemperature();
    float pressurePa = bme.readPressure();
    float humidity = bme.readHumidity();

    float tempF = tempC * 1.8 + 32.0F;
    float pressureHpa = pressurePa / 100.0F;
    
    doc["topic"] = TOPIC;
    doc["celcius"] = roundf(tempC * 100.0) / 100.0;
    doc["fahrenheit"] = roundf(tempF * 100.0) / 100.0;
    doc["pressure"] = roundf(pressureHpa * 100.0) / 100.0;
    doc["humidity"] = roundf(humidity * 100.0) / 100.0;

    String output;
    serializeJson(doc, output);

    int httpCode = http.POST(output);
    
    if (httpCode > 0) {
        logMessage("Payload sent. C:%.2f, F:%.2f, hPa:%.2f, H:%.2f\n", 
                   (float)doc["celcius"], 
                   (float)doc["fahrenheit"], 
                   (float)doc["pressure"], 
                   (float)doc["humidity"]);
    }

    String payload = http.getString();
    payload.trim();
    payload.replace("\n", "");
    payload.replace("\r", "");

    logMessage("[HTTP] Code=%d  Response: %s\n", httpCode, payload.c_str());

    if(httpCode > 0) {
      failedRequests = 0;
    } else {
      failedRequests++;
    }
    
    http.end();
  } else {
    logMessage("[HTTP] Unable to connect\n");
    failedRequests++;
  }

  if(failedRequests >= MAX_FAILED_REQUESTS) {
    logMessage("Max failed requests reached. Restarting...\n");
    delay(1000);
    ESP.restart();
  }
}


void setup() {
  Serial.begin(115200);
  while (!Serial) { delay(10); }
  logMessage("\nBooting...");

  if (!server_ip.fromString(SERVER_IP)) {
      logMessage("FATAL: Could not parse SERVER_IP address. Halting.");
      while (true) { delay(1000); }
  }

  Wire.begin();

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  WiFi.setAutoReconnect(true);
  WiFi.persistent(true);

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
  ArduinoOTA.onStart([]() { logMessage("OTA Update: Start"); });
  ArduinoOTA.onEnd([]() { logMessage("\nOTA Update: End"); });
  ArduinoOTA.onProgress([](unsigned int p, unsigned int t) { logMessage("OTA Progress: %u%%\r", (p / (t / 100))); });
  ArduinoOTA.onError([](ota_error_t error) { logMessage("OTA Error[%u]", error); });
  ArduinoOTA.begin();
  logMessage("OTA Ready. Hostname: %s\n", ota_hostname);
  logMessage("------------------------------------");
}


void loop() {
  ArduinoOTA.handle();
  unsigned long currentMillis = millis();

  if (currentMillis - previousMillis >= INTERVAL) {
      previousMillis = currentMillis;
      sendDataToServer();
  }
}