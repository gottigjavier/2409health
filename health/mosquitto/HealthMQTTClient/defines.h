/****************************************************************************************************************************
  defines.h for ESP8266 HealthMQTTClient
  
  Based on and modified for Javier Gottig
  Licensed under MIT license
 *****************************************************************************************************************************/

// Wi-Fi and MQTT conection

const char* ssid = "SSID";
const char* wifipass = "wifi password";
const char* broker = "192.168.0.36";
const char* device = "Board of Room: 1"; // Put the room number to identify the device.
const int port = 1883;


// Source of the active signal. To configure the Json
const String bed1 = "1";
const String bed2 = "2";
const String bed3 = "3";
const String bed4 = "4";
const String bed5 = "5";
const String bed6 = "6";
const String room = "1";
const String key = "this&is$a$key&to?prevent?hacking";


// Push Buttons connection
//const int pinBed1 = 5; // GPIO5 - D1
//const int pinBed2 = 4; // GPIO4 - D2
const int bit1 = 14; // GPIO14 - D5
const int bit2 = 12; // GPIO12 - D6
const int bit3 = 13; // GPIO13 - D7

// beds
const int callBed1 = 1;
const int callBed2 = 2;
const int callBed3 = 3;
const int callBed4 = 4;
const int callBed5 = 5;
const int callBed6 = 6;
const int roomReset = 0;


// Debounce delay
const int debDelay = 1000;
