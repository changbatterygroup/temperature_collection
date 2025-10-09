#include "DHT.h"

// NOTE: In order to capture temp data, connect CoolTerm to the port that the arduino is on.
#define DHTPIN 2
#define DHTTYPE DHT11

DHT dht(DHTPIN,DHTTYPE);


void setup() {
  Serial.begin(9600);
  dht.begin();
}

void loop() {
  float humi  = dht.readHumidity();
  float tempF = dht.readTemperature(true);
  float tempC = dht.readTemperature();
  Serial.print(tempF);
  Serial.print(",");
  Serial.print(tempC);
  Serial.print(",");
  Serial.print(humi);
  Serial.print("\n");
  
  delay(30000);
}
