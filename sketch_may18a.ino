#include "HX711.h"

// HX711 pins connected to your Arduino/KR-duino
#define DT_PIN 3
#define SCK_PIN 2

HX711 scale;

void setup() {
  Serial.begin(115200);

  // Optional for Leonardo-style boards:
  // Wait until Serial Monitor is opened.
  while (!Serial) {
    ; 
  }

  Serial.println("HX711 Raw Data Test");

  scale.begin(DT_PIN, SCK_PIN);

  if (scale.is_ready()) {
    Serial.println("HX711 is ready.");
  } else {
    Serial.println("HX711 not found. Check DT/SCK wiring.");
  }
}

void loop() {
  if (scale.is_ready()) {
    long rawReading = scale.read();

    Serial.print("Raw reading: ");
    Serial.println(rawReading);
  } else {
    Serial.println("HX711 not ready.");
  }

  delay(2000);
}