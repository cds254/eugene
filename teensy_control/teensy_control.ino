#include <Servo.h>

// LED pin 
int LED = 13;

// Motor pins for direction
int FL_DIR = 7;
int BL_DIR = 9;
int FR_DIR = 8;
int BR_DIR = 10;

// Motor pins for speed
int FL_PWM = 3;
int BL_PWM = 5;
int FR_PWM = 4;
int BR_PWM = 6;

// Motor pins for encoders
int FL_ENC = 17;
int BL_ENC = 16;
int FR_ENC = 15;
int BR_ENC = 14;

// VEX claw pins
int clawPin = 23;
int armPin  = 22;
Servo CLAW;
Servo ARM;

// Camera servo
int cameraPin = 21;
Servo CAMERA;

// Temp vars for reading data
char tmp;
char tmp1;
char tmp2;
char tmp3;

// Data storage;
int data[50];

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

  digitalWrite(LED, LOW);

  CLAW.attach(clawPin);
  ARM.attach(armPin);
  
  CAMERA.attach(cameraPin);
  
  // Set claw and arm to not moving
  CLAW.writeMicroseconds(1500);
  ARM.writeMicroseconds(1500);
  
  CAMERA.writeMicroseconds(1500);
  
  Serial.begin(9600);

}

int charToInt(char x) {
  switch(x) {
    case '0':
      Serial.write('0');
      return 0;
    case '1':
      Serial.write('1');
      return 1;
    case '2':
      Serial.write('2');
      return 2;
    case '3':
      Serial.write('3');
      return 3;
    case '4':
      Serial.write('4');
      return 4;
    case '5':
      Serial.write('5');
      return 5;
    case '6':
      Serial.write('6');
      return 6;
    case '7':
      Serial.write('7');
      return 7;
    case '8':
      Serial.write('8');
      return 8;
    case '9':
      Serial.write('9');
      return 9;
    case '\n':
      return -1;
  }
}


void readSerial(int DATASIZE) {  
  for (int i = 0; i < DATASIZE; i++) {
    data[i] = charToInt(Serial.read());
  }
  
//  char junk = Serial.read();        // Clear out the new line left in serial
}

void driveControl() {
  digitalWrite(FL_DIR, data[0]);
  analogWrite(FL_PWM, data[1] * 100 + data[2] * 10 + data[3]);
  
  digitalWrite(BL_DIR, data[4]);
  analogWrite(BL_PWM, data[5] * 100 + data[6] * 10 + data[7]);
    
  digitalWrite(FR_DIR, data[8]);
  analogWrite(FR_PWM, data[9] * 100 + data[10] * 10 + data[11]);
    
  digitalWrite(BR_DIR, data[12]);
  analogWrite(BR_PWM, data[13] * 100 + data[14] * 10 + data[15]);
}

void clawControl() {
  CLAW.writeMicroseconds(data[0] * 1000 + data[1] * 100 + data[2] * 10 + data[3]);
}

void armControl() {
  ARM.writeMicroseconds(data[0] * 1000 + data[1] * 100 + data[2] * 10 + data[3]);
}

void cameraControl() {
  CAMERA.writeMicroseconds(data[0] * 1000 + data[1] * 100 + data[2] * 10 + data[3]);
}

void loop() { 
  if (Serial.available() > 0) {    // a full update is available in serial
    switch(charToInt(Serial.read()))
    {
      case 0:                      // Drive Control
        readSerial(16);
        driveControl();
        break;
      case 1:                      // Claw control
        readSerial(4);
        clawControl();
        break;
      case 2:                      // Arm control
        readSerial(4);
        armControl();
      case 3:                      // Front Camera
        readSerial(4);
        cameraControl();
        break;
      case 4:                      // LED ON or OFF
        if (Serial.read() == '1') {
          digitalWrite(LED, HIGH);
        } else {
          digitalWrite(LED, LOW);
        }
        break;
      default:
        break;
    }
  }
}

