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
    case '\n':
      return -1;
  }
}


int* readSerial() {
  int data[DATASIZE];
  
  for (int i = 0; i < DATASIZE; i++) {
    data[i] = charToInt(Serial.read());
  }
  
  char junk = Serial.read();        // Clear out the new line left in serial
  
  return data;
}


void loop() {
  
  if (Serial.available() > 0) {    // a full update is available in serial
    int *ctrl = readSerial();
  
    digitalWrite(FL_DIR, ctrl[0]);
    analogWrite(FL_PWM, ctrl[1] * 100 + ctrl[2] * 10 + ctrl[3]);
 
    digitalWrite(BL_DIR, ctrl[4]);
    analogWrite(BL_PWM, ctrl[5] * 100 + ctrl[6] * 10 + ctrl[7]);
    
    digitalWrite(FR_DIR, ctrl[8]);
    analogWrite(FR_PWM, ctrl[9] * 100 + ctrl[10] * 10 + ctrl[11]);
    
    digitalWrite(BR_DIR, ctrl[12]);
    analogWrite(BR_PWM, ctrl[13] * 100 + ctrl[14] * 10 + ctrl[15]);
}

