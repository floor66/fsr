int sensorPins[] = {0, 1, 2, 3, 4, 5};
int sensorVal = 0;
int sensorCount = sizeof(sensorPins) / sizeof(int);
unsigned long t = 0;

void setup()
{
  Serial.begin(9600); //TODO: increase baud rate!
  Serial.println(" ");

  // Initialize pins
  for(int i = 0; i < sensorCount; i++) {
    pinMode(sensorPins[i], INPUT);
    Serial.print("Initialized sensor on pin ");
    Serial.println(sensorPins[i]);
  }

  Serial.println("INIT_COMPLETE");
}

void loop()
{
  // Key: time (ms), pin number (A0-5), resistor value (0-1024)

  for(int i = 0; i < sensorCount; i++) {
    t = millis();
    analogRead(sensorPins[i]);
    sensorVal = analogRead(sensorPins[i]);
    Serial.print(t);
    Serial.print(",");
    Serial.print(sensorPins[i]);
    Serial.print(",");
    Serial.println(sensorVal);
  }
}
