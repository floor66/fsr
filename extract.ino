int resistorPin = 0;
int ledPin = 3;
int resVal = 0;
unsigned long t = 0;

void setup()
{
  // Setup
  Serial.begin(9600);
  pinMode(resistorPin, INPUT);
  Serial.println(" ");
  //Key: time (ms), pin number (A0-5), resistor value (0-1024)
}

void loop()
{
  // Loop
  resVal = analogRead(resistorPin);
  t = millis();
  
  Serial.print(t);
  Serial.print(",");
  Serial.print(resistorPin);
  Serial.print(",");
  Serial.println(resVal);
}
