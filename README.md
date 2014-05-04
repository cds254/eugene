eugene
======

This is all of the software that was written for Boeing Team 3's senior design project, Spring 2014. 

linuxClient.py      - to be run on a linux client, interfaces with an xBox 360 controller and is used to communicate with rpiServer.py

rpiServer.py        - to be run on the Raspberry PI, communicates with linuxClient.py and teensy_control.ino

tennsy_control.ino  - program that is running on the teensy 3.1, communicates with rpiServer.py and controls the motors and servos on Eugene along with reading sensor data
