// =========================================================== MQTT :
#include <PubSubClient.h>

// ===========================================================
#include <PinButton.h>
#include <ESP8266WiFi.h>
#include "MyWifi.h"

// =========================================================== OTA :
#include <ESP8266mDNS.h>

#include <WiFiUdp.h>
#include <ArduinoOTA.h>

// =========================================================== BME 280 :
#include <Wire.h>
#include <SPI.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>

#define BME_SCK 13
#define BME_MISO 12
#define BME_MOSI 11
#define BME_CS 10
#define SEALEVELPRESSURE_HPA (1013.25)

Adafruit_BME280 bme; // I2C


// =========================================================== Web Server :

#include <ESP8266WebServer.h>
ESP8266WebServer server(80);

String texteJSON() {
    String message = R"({"body":{"meteo":{"humidity": )";
    message += bme.readHumidity();
    message += ",\"temperature\": ";
    message += bme.readTemperature();
    message += ",\"altitude\": ";
    message += bme.readAltitude(1013.25);
    message += ",\"pressure\": ";
    message += (bme.readPressure() / 100.0F);
    message += "}}}";

    return message;
}

void handleRoot() {
  server.send(200, "text/plain", "Salut, je suis le serveur du ESP 8266 - Arduino IDE CPP");
}

void meteoJSON() {
  String r = texteJSON();
  server.send(200, "text/plain", r);
}

void handleNotFound() {
  String message = "File Not Found\n\n";
  message += "URI: ";
  message += server.uri();
  message += "\nMethod: ";
  message += (server.method() == HTTP_GET) ? "GET" : "POST";
  message += "\nArguments: ";
  message += server.args();
  message += "\n";
  
  for (uint8_t i = 0; i < server.args(); i++) {
    message += " " + server.argName(i) + ": " + server.arg(i) + "\n";
  }
  
  server.send(404, "text/plain", message);
}

// ===========================================================


bool alert = true;

PinButton button(14); // D5

const char* ssid = STASSID;
const char* password = STAPSK;
const char* mqtt_server = MQTTSERVER;
const char* mqtt_user = MQTT_USERNAME;
const char* mqtt_password = MQTT_PASSWORD;

WiFiClient espClient;
PubSubClient client(espClient);
unsigned long lastMsg = 0;
#define MSG_BUFFER_SIZE  (50)
char msg[MSG_BUFFER_SIZE];
int value = 0;

void setup_wifi() {

  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  randomSeed(micros());

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    
    // Create a random client ID
    String clientId = "ESP8266Client-";
    clientId += String(random(0xffff), HEX);
    //Serial.println(clientId);
    if (client.connect(clientId.c_str(), mqtt_user, mqtt_password)) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);

  // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ BME 280 :
  unsigned status;
  status = bme.begin(0x76); 

  // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ MQTT :
  setup_wifi();
  client.setServer(mqtt_server, 1883);

  // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ OTA :
  ArduinoOTA.onStart([]() {
    String type;
    if (ArduinoOTA.getCommand() == U_FLASH) {
      type = "sketch";
    } else {
      type = "filesystem";
    }
    Serial.println("Start updating " + type);
  });
  ArduinoOTA.onEnd([]() {
    Serial.println("\nEnd");
  });
  ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
    Serial.printf("Progress: %u%%\r", (progress / (total / 100)));
  });
  ArduinoOTA.onError([](ota_error_t error) {
    Serial.printf("Error[%u]: ", error);
    if (error == OTA_AUTH_ERROR) {
      Serial.println("Auth Failed");
    } else if (error == OTA_BEGIN_ERROR) {
      Serial.println("Begin Failed");
    } else if (error == OTA_CONNECT_ERROR) {
      Serial.println("Connect Failed");
    } else if (error == OTA_RECEIVE_ERROR) {
      Serial.println("Receive Failed");
    } else if (error == OTA_END_ERROR) {
      Serial.println("End Failed");
    }
  });
  ArduinoOTA.begin();

  // Web serveur :
  server.on("/", handleRoot);
  server.onNotFound(handleNotFound);
  server.on("/meteoJSON", meteoJSON);
  server.begin();
}

void loop() {
  // Web serveur :
  server.handleClient();
  MDNS.update();

  ArduinoOTA.handle();
  
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  
  button.update();

  if(alert == true){
    snprintf (msg, MSG_BUFFER_SIZE, "Upload complete . . . ");
    client.publish("bme280", msg);
    alert = false;
  }
  
  if(button.isSingleClick()){
    snprintf (msg, MSG_BUFFER_SIZE, "%s %s %s %s", (String)bme.readTemperature(), (String)(bme.readPressure() / 100.0F), (String)bme.readAltitude(1013.25), (String)bme.readHumidity());
    Serial.print("Publish message: ");
    Serial.println(msg);
    client.publish("bme280", msg);
  }
}
