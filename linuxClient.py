#!/usr/bin/python2.7

import sys
import os
import socket
import select
import threading
import time
import getopt
import pygtk
import gtk
import gobject
import pygst
import gst
import pygame
from pygame.locals import *
from thread import *
from collections import deque

gobject.threads_init()

RHOST = ''			# Get host IP from args
CPORT = 7268			# Control port used by Eugene
VPORT = 7269			# Video port

readQue  = deque()		# Que for data read from the socket
writeQue = deque()		# Que for data to be sent through the socket

readLock  = threading.Lock();	# Lock for readQue
writeLock = threading.Lock();	# Lock for writeQue


class GTK_Main:

        def __init__(self):
                window = gtk.Window(gtk.WINDOW_TOPLEVEL)
                window.set_title("Eugene")
                window.set_default_size(640, 480)
                window.connect("destroy", gtk.main_quit, "WM destroy")
                vbox = gtk.VBox()
                window.add(vbox)
                self.movie_window = gtk.DrawingArea()
                vbox.add(self.movie_window)
                window.show_all()

                # Set up the gstreamer pipeline
                pipeline  = 'udpsrc port=7269 ! application/x-rtp,media=(string)video,clock-rate=(int)90000,encoding-name=(string)H264,payload=(int)96 ! '
                pipeline += 'gstrtpjitterbuffer mode=slave latency=200 drop-on-latency=true ! rtph264depay ! video/x-h264,width=640,height=480, framerate=30/1 ! '
                pipeline += 'ffdec_h264 ! ffmpegcolorspace ! autovideosink'

                self.player = gst.parse_launch(pipeline)

                bus = self.player.get_bus()
                bus.add_signal_watch()
                bus.enable_sync_message_emission()
                bus.connect("message", self.on_message)
                bus.connect("sync-message::element", self.on_sync_message)

                self.player.set_state(gst.STATE_PLAYING)

		print 'Set state to playing'

        def exit(self, widget, data=None):
                gtk.main_quit()

        def on_message(self, bus, message):
                t = message.type
                if t == gst.MESSAGE_EOS:
                        self.player.set_state(gst.STATE_NULL)
                elif t == gst.MESSAGE_ERROR:
                        err, debug = message.parse_error()
                        print "Error: %s" % err, debug
                        self.player.set_state(gst.STATE_NULL)

        def on_sync_message(self, bus, message):
                if message.structure is None:
                        return
                message_name = message.structure.get_name()
                if message_name == "prepare-xwindow-id":
                        # Assign the viewport
                        imagesink = message.src
                        imagesink.set_property("force-aspect-ratio", True)
                        imagesink.set_xwindow_id(self.movie_window.window.xid)


def tankDrive(x, y):				# Idea/explination from goodrobot.com/en/2009/09/tank-drive-via-joystick-control/
	# Compute angle in deg
	z = math.sqrt(x*x + y*y)		# first get hypotenuse
	
	if z == 0:
		z = 0.001
	
	rad = math.acos(abs(x)/z)		# then angle in rad
	angle = rad*180/math.pi			# then in deg

	# Calculate measure of turn
	tcoeff = -1 + (angle/90) * 2
	turn = tcoeff * abs(abs(y) - abs(x))
	turn = round(turn*100)/100

	# Max of x or y is movement
	move = max(abs(y), abs(x))

	# Get first and thirt quadrent
	if (x >= 0 and y >= 0) or (x < 0 and y < 0):
		left = move
		right = turn
	else:
		right = move
		left = turn

	# Reverse polarity
	if y < 0:
		left = 0 - left
		right = 0 - right

	return (left, right)


# Send data to the server.
def sendData(conn):
	conn.sendall('T')
	while 1:
		if len(writeQue) > 0:
			writeLock.acquire()
			conn.sendall(writeQue.popleft())
			writeLock.release()

		time.sleep(0)


# Receive data from the server.
def receiveData(conn):
	conn.sendall('R')
	while 1:
		data = conn.recv(1)

		if data:
			readLock.acquire()
			readQue.append(data)
			readLock.release()
			data = ''

		time.sleep(0)

def handleJoystick():
	global writeLock
	global readLock
	global writeQue
	global readQue
	
	loop = True

	LTRACK = 0
	RTRACK = 0
	LHORZ  = 0
	LVERT  = 0
	LTRIG  = 0
	RHORZ  = 0
	RVERT  = 0
	RTRIG  = 0

	pygame.init()
	
	screen = pygame.display.set_mode((320,240))
	pygame.display.set_caption("Joystick Testing")

	joystick = pygame.joystick.Joystick(0)
	joystick.init()

	clock = pygame.time.Clock()
	
	# Read/write joystick/terminal <-> sockets
	while loop:
		clock.tick(2)
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				print "Quitting"
				loop = False
			elif event.type == JOYAXISMOTION:
				if event.axis == 0:		# Left stick horizontal
					LHORZ = joystick.get_axis(event.axis)
					if LHORZ > 1:
						LHORZ = 1
					elif LHORZ < -1:
						LHORZ = -1
					elif LHORZ > (-1 * ZERO_BUFF) and LHORZ < ZERO_BUFF:
						LHORZ = 0
					print 'LHORZ: ' + str(LHORZ)
				elif event.axis == 1:		# Left stick vertical
					LVERT = joystick.get_axis(event.axis) * -1	# Gives axis backward origionally
					if LVERT > 1:
						LVERT = 1
					elif LVERT < -1:
						LVERT = -1
					elif LVERT > (-1 * ZERO_BUFF) and LVERT < ZERO_BUFF:
						LVERT = 0
					print 'LVERT: ' + str(LVERT)
				elif event.axis == 2:		# Left trigger
					LTRIG = joystick.get_axis(event.axis)
				elif event.axis == 3:		# Right stick horizontal
					RHORZ = joystick.get_axis(event.axis)
				elif event.axis == 4:		# Right stick vertical
					RVERT = joystick.get_axis(event.axis)
				elif event.axis == 5:		# Right triger
					RTRIG = joystick.get_axis(event.axis)


			elif event.type == JOYBUTTONDOWN:
				time.sleep(0)
			elif event.type == JOYBUTTONUP:
				time.sleep(0)
				
		LTRACK, RTRACK = tankDrive(LHORZ, LVERT)

		# Calculate move F/B and magnatudew
		LPWM = LTRACK * 255
		RPWM = RTRACK * 255

		if LTRACK <= 0:
			FLDIR = 0
			BLDIR = 1
		else:
			FLDIR = 1
			BLDIR = 0

		if RTRACK <= 0:
			FRDIR = 0
			BRDIR = 1
		else:
			FRDIR = 1
			BRDIR = 0
			
		oldState = state
		state = ((FLDIR,LPWM),(BLDIR,LPWM),(FRDIR,RPWM),(BRDIR,RPWM))

		if oldState != state:			# If the state has changed, push it to the socket
			writeLock.acquire()
			writeQue.append(str(state[0][0]))
			writeQue.append(str(state[0][1].zfill(3)))
			writeQue.append(str(state[1][0]))
			writeQue.append(str(state[1][1].zfill(3)))		
			writeQue.append(str(state[2][0]))
			writeQue.append(str(state[2][1].zfill(3)))
			writeQue.append(str(state[3][0]))
			writeQue.append(str(state[3][1].zfill(3)))
			writeLock.release()

		if len(readQue) > 0:				# If there is data to be written to stdo
			readLock.acquire()
			sys.stdout.write(readQue.popleft())	# Write it to stdout
			sys.stdout.flush()
			readLock.release()

		time.sleep(0)


def main(argv):
	# Argument handeling - clean up sometime when it isn't 6am
	try:
		opts, args = getopt.getopt(argv, "i:");
	except getopt.GetoptError:
		print 'linuxClient.py -i <ip_addr>'
		sys.exit(2)

	for o, a in opts:
		if o == '-i':
			RHOST = a

#	start_new_thread(rxVideo, (VPORT,))
	print 'Started video thread.'

	# Set up connections and spawn threads to do socket read and write.
	try:
		conn1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		conn2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	except socket.error, msg:
		print 'Failed to create socket. Error code: ' + str(msg[0]) + ' Error message: ' + msg[1]
		sys.exit(2)

	print 'Sockets created.'

	conn1.connect((RHOST, CPORT))
	conn2.connect((RHOST, CPORT))

	print 'Sockets connected to host.'

	start_new_thread(sendData, (conn1,))
	start_new_thread(receiveData, (conn2,))
	start_new_thread(handleJoystick, ())

	print 'Spawned threads.'

	GTK_Main()
	gtk.gdk.threads_init()
	gtk.main()


if __name__ == '__main__':
	main(sys.argv[1:])
