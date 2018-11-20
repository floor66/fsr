/*
    extract.ino
    Created by Floris P.J. den Hartog, 2018

    Gathering of "raw" Force Sensitive Resistor data from analog input
    Configurable measurement frequency
    Note: higher frequencies (>200) might not play nice with python
*/

int sensorPins[] = {0, 1, 2, 3, 4, 5};
unsigned long timers[] = {0, 0, 0, 0, 0, 0};
int sensorVal = 0;
int sensorCount = sizeof(sensorPins) / sizeof(int);
int MEASUREMENT_FREQ = 100; // Measurement frequency (Hz)
unsigned long curr_t = 0;
unsigned long tmp_t = 0;

void setup()
{
  Serial.begin(250000);
  Serial.println(" ");

  // Initialize pins
  for(int i = 0; i < sensorCount; i++) {
    pinMode(sensorPins[i], INPUT);
    Serial.print("Initialized on pin ");
    Serial.println(sensorPins[i]);
  }

  Serial.println("INIT_COMPLETE");
}

void loop()
{
  // Key: time (ms), pin number (A0-5), resistor value (0-1023)

  for(int i = 0; i < sensorCount; i++) {
    curr_t = millis();
    tmp_t = timers[i];

    if(!((curr_t - tmp_t) >= (1000 / MEASUREMENT_FREQ))) {
      continue;
    }
    
    analogRead(sensorPins[i]);
    sensorVal = analogRead(sensorPins[i]);
    timers[i] = curr_t;
    Serial.print(curr_t);
    Serial.print(",");
    Serial.print(sensorPins[i]);
    Serial.print(",");
    Serial.println(sensorVal);

    // Debugging only
    //Serial.print("ms diff: ");
    //Serial.println(curr_t - tmp_t);
  }
}
