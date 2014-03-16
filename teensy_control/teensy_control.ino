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

void loop() {  
  digitalWrite(FL_DIR, HIGH);
  digitalWrite(BL_DIR, LOW);
  digitalWrite(FR_DIR, HIGH);
  digitalWrite(BR_DIR, LOW);
  
  analogWrite(FL_PWM, 200);
  analogWrite(BL_PWM, 200);
  analogWrite(FR_PWM, 200);
  analogWrite(BR_PWM, 200);
}
