#!/usr/bin/python2.7

import sys
import os
import math
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
import gobject
from pygame.locals import *
from thread import *
from collections import deque

gobject.threads_init()

RHOST  = ''			# Get host IP from args
CPORT  = 7268			# Control port used by Eugene
VPORT  = 5000			# Video port
VPORT2 = 5001			# Video port

hallData1  = ""			# Current reading from hall Effect Sensor 1
hallData2  = ""			# Current reading from hall Effect Sensor 2

readLock  = threading.Lock()	# Lock for readQue

driveState = (0,0)		# Current driving state (prevents sending redundant data)
clawState  = (0,0)		# Current claw state    (prevents sending redundant data)
armState   = (0,0)		# Current arm state     (prevents sending redundant data)

lights = False
switchActive = True

class GTK_Main:

        def __init__(self, timeout):
                self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
                
		self.window.set_title("Eugene")
		self.window.set_default_size(1366,768)
		self.window.set_decorated(False)
		self.window.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("#2D2F31"))

                self.window.connect("destroy", gtk.main_quit, "WM destroy")
                
		table = gtk.Table(12, 16, True)
                self.window.add(table)
                
		self.front_cam_window = gtk.DrawingArea()
		self.back_cam_window  = gtk.DrawingArea()
                
		self.vbox = gtk.VBox()

		self.hall1  = gtk.Label("Hall Effect 1:")
		self.hall2  = gtk.Label("Hall Effect 2:")
		self.lights = gtk.Label("Lights On:")
		self.armS   = gtk.Label("Arm Switch Active:")

		self.vbox.pack_start(self.hall1)
		self.vbox.pack_start(self.hall2)
		self.vbox.pack_start(self.lights)
		self.vbox.pack_start(self.armS)

		table.attach(self.front_cam_window, 4, 12, 2, 10)
		table.attach(self.back_cam_window, 0, 4, 0, 4)
		table.attach(self.vbox, 13, 14, 5, 6)
                
		self.window.show_all()

                # Set up the gstreamer pipeline
                pipeline  = 'udpsrc port=' + str(VPORT)
                pipeline += ' ! application/x-rtp,media=video,clock-rate=90000,encoding-name=JPEG,payload=96 ! rtpjpegdepay ! decodebin ! autovideosink'
                
                pipeline2  = 'udpsrc port=' + str(VPORT2)
                pipeline2 += ' ! application/x-rtp,media=video,clock-rate=90000,encoding-name=JPEG,payload=96 ! rtpjpegdepay ! decodebin ! autovideosink'
		
                self.front_cam = gst.parse_launch(pipeline)
                self.back_cam = gst.parse_launch(pipeline2)

                front_bus = self.front_cam.get_bus()
                front_bus.add_signal_watch()
                front_bus.enable_sync_message_emission()
                front_bus.connect("message", self.on_message_front)
                front_bus.connect("sync-message::element", self.on_sync_message_front)
                
		back_bus = self.back_cam.get_bus()
                back_bus.add_signal_watch()
                back_bus.enable_sync_message_emission()
                back_bus.connect("message", self.on_message_back)
                back_bus.connect("sync-message::element", self.on_sync_message_back)

                self.front_cam.set_state(gst.STATE_PLAYING)
                
		self.back_cam.set_state(gst.STATE_PLAYING)

		print 'Set state to playing'
	
	        gobject.timeout_add_seconds(timeout, self.updateText)		# Call updateText every timeout seconds

	def updateText():
		global lights
		global switchActive
		print "updating text"
	
		readLock.acquire()
		self.hall1.set_label("Hall Effect 1: " + hallData1)
		self.hall2.set_label("Hall Effect 2: " + hallData2)
		readLock.release()
		
		self.lights.set_label("Lights On: " + str(lights))
		self.armS   = gtk.Label("Arm Switch Active: " + str(switchActive))

		return True		# Required to get the timer to call again

	def exit(self, widget, data=None):
                gtk.main_quit()

        def on_message_front(self, bus, message):
                t = message.type
                if t == gst.MESSAGE_EOS:
                        self.front_cam.set_state(gst.STATE_NULL)
                elif t == gst.MESSAGE_ERROR:
                        err, debug = message.parse_error()
                        print "Error: %s" % err, debug
                        self.front_cam.set_state(gst.STATE_NULL)
        
	def on_message_back(self, bus, message):
                t = message.type
                if t == gst.MESSAGE_EOS:
                        self.back_cam.set_state(gst.STATE_NULL)
                elif t == gst.MESSAGE_ERROR:
                        err, debug = message.parse_error()
                        print "Error: %s" % err, debug
                        self.back_cam.set_state(gst.STATE_NULL)

        def on_sync_message_front(self, bus, message):
		if message.structure is None:
                        return
                message_name = message.structure.get_name()
                if message_name == "prepare-xwindow-id":
                        # Assign the viewport
                        message.src.set_property("force-aspect-ratio", True)
                        message.src.set_xwindow_id(self.front_cam_window.window.xid)
        
	def on_sync_message_back(self, bus, message):
                if message.structure is None:
                        return
                message_name = message.structure.get_name()
                if message_name == "prepare-xwindow-id":
                        # Assign the viewport
                        message.src.set_property("force-aspect-ratio", True)
                        message.src.set_xwindow_id(self.back_cam_window.window.xid)


def tankDrive(x, y):
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
		right = move
		left = turn
	else:
		left = move
		right = turn

	# Reverse polarity
	if y < 0:
		left = 0 - left
		right = 0 - right

	return (left, right)


# Receive data from the server.
def receiveData(conn):
	global hallData1
	global hallData2

	conn.sendall('R')
	
	while 1:
		data = 'a'
		while data[-1] != '\n':
			data += conn.recv(1)

		readLock.acquire()
		if data[1:2] == 'h1':
			hallData1 = data[3:-1]
		elif data[1:2] == 'h2':
			hallData2 = data[3:-1]
		readLock.release()
		
		print data[1:-1]

		time.sleep(0)


def handleJoystick(conn):
	global lights
	global switchActive
	
	loop = True

	LTRACK = 0.0
	RTRACK = 0.0
	LHORZ  = 0.0
	LVERT  = 0.0
	LTRIG  = 0.0
	RHORZ  = 0.0
	RVERT  = 0.0
	RTRIG  = 0.0

	camAngle = 1500		# Initial angle of camera (PWM from 0 - 3k)
	camTurn  = 10		# Ammount to turn every time the button is polled as down 
	
	conn.sendall('T')	# Let the server know we are transmitting data on this connection.

	# Initialize controller
	conn.sendall('01000000010000000\n')	# Driving set to 0
	conn.sendall('11500\n')			# Claw set to no movement
	conn.sendall('21500\n')			# Arm set to no movement
	conn.sendall('33\n')			# Front Camera Centered
	conn.sendall('40\n')			# LEDs off
	conn.sendall('61\n')			# Arm Switch On

	lights = False				# Redundant but makes me feel better
	switchActive = True			# Redundant for the same reason

	pygame.init()
	
	joystick = pygame.joystick.Joystick(0)
	joystick.init()

	clock = pygame.time.Clock()
			
	# Read/write joystick/terminal <-> sockets
	while loop:
		clock.tick(60)
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				print "Quitting"
				loop = False
			elif event.type == JOYAXISMOTION:
				if event.axis == 0:		# Left stick horizontal
					LHORZ = joystick.get_axis(event.axis)
				elif event.axis == 1:		# Left stick vertical
					LVERT = joystick.get_axis(event.axis) * -1	# Gives axis backwords origionally
				elif event.axis == 2:		# Left trigger
					LTRIG = joystick.get_axis(event.axis)
				elif event.axis == 3:		# Right stick horizontal
					RHORZ = joystick.get_axis(event.axis)
				elif event.axis == 4:		# Right stick vertical
					RVERT = joystick.get_axis(event.axis)
				elif event.axis == 5:		# Right triger
					RTRIG = joystick.get_axis(event.axis)

			elif event.type == JOYBUTTONDOWN:
				if event.button == 0:		# Button A - reset camera position
					conn.sendall("33\n")
				elif event.button == 1:		# Button B - disable Arm Switch
					if switchActive == True:
						switchActive = False
						conn.sendall("62\n")
					else:
						switchActive = True
						conn.sendall("61\n")
				elif event.button == 2:		# Button X - lights on
					if lights:
						conn.sendall("40\n")
						lights = False
						print "Sent lights on"
					else:
						conn.sendall("41\n")
						print "Sents lights off"
						lights = True
				elif event.button == 3:		# Button Y - deposit block
					conn.sendall("5\n")
				elif event.button == 4:		# Button LB - pan left
					conn.sendall("32\n")
				elif event.button == 5:		# Button RB - pan right
					conn.sendall("31\n")
			elif event.type == JOYBUTTONUP:
				if event.button == 4:		# Button LB - stop pan
					conn.sendall("30\n")
				elif event.button == 5:		# Button RB - stop pan
					conn.sendall("30\n")
		
		toSend = ''

		tmp = drive(LHORZ, LVERT)			# Calc driving stuff
		if tmp != '':
			toSend += '0' + str(tmp)
		
		tmp = claw(LTRIG, RTRIG)			# Calc claw stuff
		if tmp != '':
			toSend += '1' + str(int(tmp))
		
		tmp = arm(RVERT)				# Calc arm stuff
		if tmp != '':
			toSend += '2' + str(int(tmp))
		
		if toSend != '':
			conn.sendall(toSend + '\n')
			sys.stderr.write('Sent: ' + toSend + '\n')

		time.sleep(0)

def claw(LTRIG, RTRIG):
	global clawState
	stall_speed = 50
	expo = 1.8

	if LTRIG > -1:				# Left trigger -> open claw
		scale = (LTRIG + 1) * .5		# scale trigger to 0-1
		scale = scale ** expo			# apply expo
		deltaClaw = scale * 500			# scale 0-1 to 0-500
		deltaClaw *= -1
	elif RTRIG > -1:			# Right trigger -> close claw
		scale = (RTRIG + 1) * .5		# scale trigger to 0-1
		scale = scale ** expo			# apply expo
		deltaClaw = scale * 500			# scale 0-1 to 0-500
	elif clawState != 0:			# Triggers released and motor has current
		deltaClaw = 0				# release current on motor
	else:					# Neither trigger -> nothing
		return ''

	if deltaClaw != clawState:
		if abs(deltaClaw) < stall_speed:
			deltaClaw = 0

		clawState = deltaClaw
		return 1500 + deltaClaw
	else:
		return ''


def arm(RVERT):
	global armState

	ZERO_BUFF = 0.15
	expo = 1.8

	if RVERT > 1:
		RVERT = 1.0
	elif RVERT < -1:
		RVERT = 1.0
	elif abs(RVERT) < ZERO_BUFF:
		RVERT = 0.0
	
	# -1 to 1 -> -500 to 500 with expo
	if RVERT < 0:
		deltaArm = -1 * (abs(RVERT) ** expo)
	else:
		deltaArm = RVERT ** expo
	
	deltaArm *= 500

	if deltaArm != armState:
		armState = deltaArm
		return 1500 + deltaArm
	else:
		return ''


def drive(LHORZ, LVERT):
	global driveState
	
	ZERO_BUFF = 0.3
	STALL_SPEED = 30
	

	if LHORZ > 1:
		LHORZ = 1.0
	elif LHORZ < -1:
		LHORZ = -1.0
			
	if LVERT > 1:
		LVERT = 1.0
	elif LVERT < -1:
		LVERT = -1.0


	if abs(LHORZ) < ZERO_BUFF and abs(LVERT) < ZERO_BUFF:
		LHORZ = LVERT = 0.0

	E_LHORZ = LHORZ * .75

	expo_horz = 1.8
	expo_vert = 1.8
	if LHORZ < 0:
		E_LHORZ = (abs(E_LHORZ) ** expo_horz) * -1		# exponential function to make control feel smooth
	else:
		E_LHORZ = E_LHORZ ** expo_horz

	if LVERT < 0:
		E_LVERT = (abs(LVERT) ** expo_vert) * -1
	else:
		E_LVERT = LVERT ** expo_vert

	LTRACK, RTRACK = tankDrive(E_LHORZ, E_LVERT)
		
	LPWM = int(LTRACK * 255)
	RPWM = int(RTRACK * 255)

	if abs(LPWM) < STALL_SPEED:
		LPWM = 0
	if abs(RPWM) < STALL_SPEED:
		RPWM = 0

	if LTRACK <= 0:
		FLDIR = 1
		BLDIR = 0
	else:
		FLDIR = 0
		BLDIR = 1

	if RTRACK <= 0:
		FRDIR = 1
		BRDIR = 0
	else:
		FRDIR = 0
		BRDIR = 1

	LPWM = abs(LPWM)
	RPWM = abs(RPWM)
		
	oldState = driveState
	driveState = str(FLDIR) + str(LPWM).zfill(3) + str(BLDIR) + str(LPWM).zfill(3) + str(FRDIR) + str(RPWM).zfill(3) + str(BRDIR) + str(RPWM).zfill(3) + '\n'

	if oldState != driveState:			# If the state has changed, push it to the socketi
		print str(driveState)
		return driveState

	return ''

def main(argv):
	# Argument handeling - clean up sometime when it isn't 6am
	try:
		opts, args = getopt.getopt(argv, "i:")
	except getopt.GetoptError:
		print 'linuxClient.py -i <ip_addr>'
		sys.exit(2)

	for o, a in opts:
		if o == '-i':
			RHOST = a

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

	start_new_thread(handleJoystick, (conn1,))
	start_new_thread(receiveData, (conn2,))

	print 'Spawned threads.'

	asdf = GTK_Main(0.1)
	gtk.gdk.threads_init()
	gtk.main()


if __name__ == '__main__':
	main(sys.argv[1:])
