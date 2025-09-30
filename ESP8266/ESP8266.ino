#include <ESP8266WiFi.h>
#include <Pinger.h> // The new library's header

// --- Configuration ---
// These values are now injected at compile-time by the Makefile.
// The preprocessor will throw an error if they are not defined.
#ifndef WIFI_SSID
  #error "WIFI_SSID is not defined. Please provide it in credentials.mk or on the command line."
#endif
#ifndef WIFI_PASS
  #error "WIFI_PASS is not defined. Please provide it in credentials.mk or on the command line."
#endif

// Use the compile-time definitions for our constants.
const char* ssid = WIFI_SSID;
const char* password = WIFI_PASS;


// Set the IP address of the Raspberry Pi you want to ping
const IPAddress pi_ip(10, 248, 204, 26); // IMPORTANT: Change this to your Pi's actual IP address

// Create a Pinger object. This needs to be global.
Pinger pinger;

void setup() {
    // Start the Serial Monitor
    Serial.begin(115200);
    while (!Serial) {
        delay(10); // wait for serial port to connect
    }
    Serial.println(); // Add a newline for clarity

    // Begin connecting to Wi-Fi
    WiFi.begin(ssid, password);

    // Wait for connection and print status
    Serial.print("Connecting to WiFi SSID: ");
    Serial.println(ssid);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }

    // --- Connection Successful ---
    Serial.println("\nWiFi connected!");
    Serial.print("ESP8266 MAC Address: ");
    Serial.println(WiFi.macAddress());
    Serial.print("Local IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.println("------------------------------------");

    // --- Configure Pinger Callbacks ---

    // This function gets called for every ping response
    pinger.OnReceive([](const PingerResponse& response) {
        if (response.ReceivedResponse) {
            Serial.printf(
                "Reply from %s: bytes=%d time=%lums TTL=%d\n",
                response.DestIPAddress.toString().c_str(),
                response.EchoMessageSize,
                response.ResponseTime,
                response.TimeToLive);
        } else {
            Serial.printf("Request timed out.\n");
        }
        // Return true to continue the ping sequence
        return true;
    });

    // This function gets called when the entire ping sequence is finished
    pinger.OnEnd([](const PingerResponse& response) {
        // Calculate packet loss
        float loss = 100;
        if (response.TotalReceivedResponses > 0) {
            loss = (response.TotalSentRequests - response.TotalReceivedResponses) * 100.0 / response.TotalSentRequests;
        }

        // Print statistics
        Serial.printf(
            "--- Ping statistics for %s ---\n",
            response.DestIPAddress.toString().c_str());
        Serial.printf(
            "%lu packets transmitted, %lu received, %.2f%% packet loss\n",
            response.TotalSentRequests,
            response.TotalReceivedResponses,
            loss);
        
        if(response.TotalReceivedResponses > 0) {
             Serial.printf(
                "round-trip min/avg/max = %lu/%f/%lu ms\n",
                response.MinResponseTime,
                response.AvgResponseTime,
                response.MaxResponseTime);
        }
        Serial.println("------------------------------------");
        return true;
    });
}

void loop() {
    Serial.printf("\nPinging Raspberry Pi at %s...\n", pi_ip.toString().c_str());
    Serial.print("Local ip: ");
    Serial.println(WiFi.localIP());
    
    // The pinger.Ping() command sends a sequence of pings (default is 5).
    // The callbacks we defined in setup() will be triggered automatically.
    // This is a blocking call and will wait until the sequence is complete.
    if (pinger.Ping(pi_ip) == false) {
        Serial.println("Error during ping command.");
    }

    // Wait for 10 seconds before starting the next ping sequence
    delay(10000);
}

