/*
  Simple serial control, move front and back.
 */

int LED = 13;

int FL_DIR = 7;
int BL_DIR = 8;
int FR_DIR = 9;
int BR_DIR = 10;

int FL_PWM = 3;
int BL_PWM = 4;
int FR_PWM = 5;
int BR_PWM = 6;

int FL_ENC = 17;
int BL_ENC = 16;
int FR_ENC = 15;
int BR_ENC = 14;

char tmp;
char tmp1;
char tmp2;
char tmp3;

// the setup routine runs once when you press reset:
void setup() {                
  // initialize the digital pin as an output.
  pinMode(LED, OUTPUT);

  pinMode(FL_DIR, OUTPUT);
  pinMode(BL_DIR, OUTPUT);
  pinMode(FR_DIR, OUTPUT);
  pinMode(BR_DIR, OUTPUT);

  pinMode(FL_PWM, OUTPUT);
  pinMode(BL_PWM, OUTPUT);
  pinMode(FR_PWM, OUTPUT);
  pinMode(BR_PWM, OUTPUT);

  pinMode(FL_ENC, OUTPUT);
  pinMode(BL_ENC, OUTPUT);
  pinMode(FR_ENC, OUTPUT);
  pinMode(BR_ENC, OUTPUT);

  Serial.begin(9600);

}

int charToInt(char x) {
  switch(x) {
    case '0':
      return 0;
    case '1':
      return 1;
    case '2':
      return 2;
    case '3':
      return 3;
    case '4':
      return 4;
    case '5':
      return 5;
    case '6':
      return 6;
    case '7':
      return 7;
    case '8':
      return 8;
    case '9':
      return 9;
  }
}

void loop() {
  digitalWrite(LED, LOW);
  
  if (Serial.available() >= 16) {    // a full update is available in serial
    digitalWrite(LED, HIGH);

    tmp  = Serial.read();
    tmp1 = Serial.read();
    tmp2 = Serial.read();
    tmp3 = Serial.read();
    
    digitalWrite(FL_DIR, tmp);
    analogWrite(FL_PWM, charToInt(tmp1) * 100 + charToInt(tmp2) * 10 + charToInt(tmp3));
    
    tmp  = Serial.read();
    tmp1 = Serial.read();
    tmp2 = Serial.read();
    tmp3 = Serial.read();
    
    digitalWrite(BL_DIR, tmp);
    analogWrite(BL_PWM, charToInt(tmp1) * 100 + charToInt(tmp2) * 10 + charToInt(tmp3));
    
    tmp  = Serial.read();
    tmp1 = Serial.read();
    tmp2 = Serial.read();
    tmp3 = Serial.read();
    
    digitalWrite(FR_DIR, tmp);
    analogWrite(FR_PWM, charToInt(tmp1) * 100 + charToInt(tmp2) * 10 + charToInt(tmp3));
    
    tmp  = Serial.read();
    tmp1 = Serial.read();
    tmp2 = Serial.read();
    tmp3 = Serial.read();
    
    digitalWrite(BR_DIR, tmp);
    analogWrite(BR_PWM, charToInt(tmp1) * 100 + charToInt(tmp2) * 10 + charToInt(tmp3));
    
  }
}

