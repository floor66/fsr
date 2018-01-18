int resistor1Pin = 0;
int resistor2Pin = 1;
int res1Val = 0;
int res2Val = 0;
unsigned long t = 0;

void setup()
{
  // Setup
  Serial.begin(9600);
  pinMode(resistor1Pin, INPUT);
  pinMode(resistor2Pin, INPUT);
  Serial.println(" ");
  //Key: time (ms), pin number (A0-5), resistor value (0-1024)
}

void loop()
{
  // Loop
  t = millis();

  res1Val = analogRead(resistor1Pin);
  Serial.print(t);
  Serial.print(",");
  Serial.print(resistor1Pin);
  Serial.print(",");
  Serial.println(res1Val);

  res2Val = analogRead(resistor2Pin);
  Serial.print(t);
  Serial.print(",");
  Serial.print(resistor2Pin);
  Serial.print(",");
  Serial.println(res2Val);
}
