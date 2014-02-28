#!/usr/bin/python2.7

import sys
import socket
import serial
import threading
import select
import time
import cv2
import pygame
from thread import *
from collections import deque

HOST = ''			# symbolic name: all available interfaces
CPORT = 7268			# Control port: RBOT - lololol
VPORT = 7269			# Video port

serialRead  = deque()		# Que for writing to serial.
serialWrite = deque()		# Que for reading from serial.

readLock  = threading.Lock()	# Lock for serialRead.
writeLock = threading.Lock()	# Lock for serialWrite.

isFirstConn = True		# First connection by the client (don't want to double stream video
loop = True			# Global thread loop flag (no need for mutex as race conditions are irrelevent)


def txVideo(IP, PORT):
	global isFirstConn

	webcam = cv2.VideoCapture(-1)           # change to -1 for pi

	time.sleep(1)				# Sleep for a second to wait for the client to get set up

	while isFirstConn == False:
		try:
			conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		except socket.error, msg:
			print "Failed to create txSocket, error code: " + str(msg[0]) + " Error message: " + msg[1]
			sys.exit(2)
		
		try:
			conn.connect((IP, PORT))
		except socket.error, e:
			print 'ERROR: ' + str(e) + '\nWaiting for client to reconnect.'
			isFirstConn = True

		if isFirstConn == False:
			_, img = webcam.read()
	        
			image_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
			data = pygame.image.frombuffer(image_rgb.tostring(), image_rgb.shape[1::-1], "RGB")
		
			conn.sendall(pygame.image.tostring(data, "RGB"))

		conn.close()
		time.sleep(0.034)


# Function for handling data recieving.
def receiveData(conn):
	# keep func/thread alive
	loop = True
	while loop:
		try:
			data = conn.recv(1)		# Recieve a byte at a time from the client
		except IOError:
			print 'IOError occured, possible broken pipe?'
			print 'Resetting and waiting for new connections.'
			loop = False
		if data:				# If no data, loop again
			writeLock.acquire()
			serialWrite.append(data)	# Otherwise, write byte to the write que
			writeLock.release()

		time.sleep(0);

	#came out of loop
	print 'Connection closed (receiveData).'
	conn.close()


# Function for data transmittion.
def transmitData(conn):
	loop = True
	while loop:
		readLock.acquire()
		if len(serialRead) > 0:					# If there is data to be sent
			try:
				conn.sendall(serialRead.popleft())	# send it
			except IOError:
				print 'IOError occured, possible broken pipe?'
				print 'Resetting and waiting for new connections.'
				loop = False

		readLock.release()

		time.sleep(0);

	#came out of loop
	print 'Connection closed (transmitData).'
	conn.close()


# Fucntion for serial communication with teensy
def serialHandler():
	s = serial.Serial('/dev/ttyACM0', 9600)

	while 1:
		if s.inWaiting() > 0:					# If there is stuff to be read, read it:
			readLock.acquire()
			serialRead.append(s.readline())			# Place it in the que for the transmitData thread.
			readLock.release()

		if len(serialWrite) > 0:				# If there is stuff to write from the receiveData thread:
			writeLock.acquire()
                        data = serialWrite.popleft()
			writeLock.release()
                        if data != '\n':
                            s.write(data)                               # Write it to the serial connection.

		time.sleep(0)


# Main
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print 'Socket created'

try:
	s.bind((HOST, CPORT))
except socket.error, msg:
	print 'Bind failed. Error Code: ' + str(msg[0]) + ' Message ' + msg[1]
	sys.exit(2)

print 'Socket bind complete'

# put socket in listening mode
s.listen(2)
print 'Socket now listening.'

# Create a thread to handel the serial connection
#start_new_thread(serialHandler, ())

# Keep accepting connections
while 1:
	# wait to accept a connection - blocking call
	conn, addr = s.accept()

	# display client information
	print 'Connected with ' + addr[0] + ':' + str(addr[1])

	data = conn.recv(1)	# Get the send/recieve flag (1 char)

	if isFirstConn:
		start_new_thread(txVideo, (addr[0], VPORT))
		isFirstConn = False

	# Start thread to handle communication
	if data == 'T':		# Host is transmitting on this socket
		start_new_thread(receiveData, (conn,))
	elif data == 'R': 	# Host is receiving on this socket
		start_new_thread(transmitData, (conn,))
	else:			# lolwat?
		conn.close()

s.close()
