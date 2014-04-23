#!/usr/bin/python2.7

import sys
import socket
import serial
import threading
import select
import time
import gi
from thread import *
from collections import deque
gi.require_version('Gst', '1.0')
from gi.repository import Gst
from gi.repository import GObject

Gst.init(None)
GObject.threads_init()

HOST   = ''			# symbolic name: all available interfaces
CPORT  = 7268			# Control port: RBOT - lololol
VPORT  = 5000			# Video port for front cam
VPORT2 = 5001			# Video port for back cam

serialRead  = deque()		# Que for writing to serial.
serialWrite = deque()		# Que for reading from serial.

readLock  = threading.Lock()	# Lock for serialRead.
writeLock = threading.Lock()	# Lock for serialWrite.

isFirstConn = True		# First connection by the client (don't want to double stream video
loop = True			# Global thread loop flag (no need for mutex as race conditions are irrelevent)


def txVideo(IP):
	time.sleep(1)
	
	# Set up the pipeline
	pipeline  = 'v4l2src device=/dev/video1 ! image/jpeg, width=640, framerate=10/1, rate=10 ! queue '
	pipeline += ' ! rtpjpegpay pt=96 ! udpsink host=' + str(IP) + ' port=' + str(VPORT)

	pipeline2  = 'v4l2src device=/dev/video0 ! image/jpeg, width=320, framerate=10/1, rate=10 ! queue '
	pipeline2 += ' ! rtpjpegpay pt=96 ! udpsink host=' + str(IP) + ' port=' + str(VPORT2)
	
	frontCamStream = Gst.parse_launch(pipeline)
	backCamStream = Gst.parse_launch(pipeline2)

	frontCamStream.set_state(Gst.State.PLAYING)
	backCamStream.set_state(Gst.State.PLAYING)

	print 'Set state to PLAYING'

	# problem with python wrapper's timed_pop_filtered not excepting GST_CLOCK_TIME_NONE
	# fix by redefining it from -1 to max time ammount 4294967295
	GST_CLOCK_TIME_NONE = 4294967295

	# Wait until error or EOS
	bus = frontCamStream.get_bus()
	bus2 = backCamStream.get_bus()

	while True:
	        msg = bus.timed_pop_filtered(GST_CLOCK_TIME_NONE, Gst.MessageType.ERROR | Gst.MessageType.EOS)
	        msg2 = bus2.timed_pop_filtered(GST_CLOCK_TIME_NONE, Gst.MessageType.ERROR | Gst.MessageType.EOS)
	        if type(msg) != type(None):
	                break
	        
		if type(msg2) != type(None):
	                break

	if msg.type == Gst.MessageType.ERROR:
	        gerror, dbg_msg = msg.parse_error()
	        print "Error         : ", gerror.message
	        print "Debug details : ", dbg_msg
	
	if msg2.type == Gst.MessageType.ERROR:
	        gerror, dbg_msg = msg2.parse_error()
	        print "Error         : ", gerror.message
	        print "Debug details : ", dbg_msg

	# Free resources
	frontCamStream.set_state(Gst.State.NULL)
	backCamStream.set_state(Gst.State.NULL)



# Function for handling data recieving.
def receiveData(conn):
	# keep func/thread alive
	loop = True
	while loop:
		data = 'a'

		try:
			while data[-1] != '\n':
				data += conn.recv(1)		# Recieve a byte at a time from the client

		except IOError:
			print 'IOError occured, possible broken pipe?'
			print 'Resetting and waiting for new connections.'
		
		
		writeLock.acquire()
		serialWrite.append(data[1:-1])	# Otherwise, write byte to the write que
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

	print "Serial handler started."

	while True:
		#if s.inWaiting() > 0:					# If there is stuff to be read, read it:
		#	readLock.acquire()
		#	serialRead.append(s.readline())			# Place it in the que for the transmitData thread.
		#	readLock.release()
		if len(serialWrite) > 0:				# If there is stuff to write from the receiveData thread:
			writeLock.acquire()
                        data = serialWrite.popleft()
			writeLock.release()
			s.write(data)

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
start_new_thread(serialHandler, ())

# Keep accepting connections
while 1:
	# wait to accept a connection - blocking call
	conn, addr = s.accept()

	# display client information
	print 'Connected with ' + addr[0] + ':' + str(addr[1])

	data = conn.recv(1)	# Get the send/recieve flag (1 char)

	if isFirstConn:
		start_new_thread(txVideo, (addr[0],))
		isFirstConn = False

	# Start thread to handle communication
	if data == 'T':		# Host is transmitting on this socket
		start_new_thread(receiveData, (conn,))
	elif data == 'R': 	# Host is receiving on this socket
		start_new_thread(transmitData, (conn,))
	else:			# lolwat?
		conn.close()

s.close()
