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


#def rxVideo(PORT):
#	pipeline  = 'udpsrc port=5000 ! application/x-rtp,media=(string)video,clock-rate=(int)90000,encoding-name=(string)H264,payload=(int)96 ! '
#	pipeline += 'gstrtpjitterbuffer mode=slave latency=200 drop-on-latency=true ! rtph264depay ! video/x-h264,width=640,height=480, framerate=30/1 ! '
#	pipeline += 'ffdec_h264 ! ffmpegcolorspace ! autovideosink'

#	camStream = gst.parse_launch(pipeline)

#	camStream.set_state(gst.STATE_PLAYING)

	# Wait until error or EOS
#	bus = camStream.get_bus()

#	while True:
#		msg = bus.timed_pop_filtered(gst.CLOCK_TIME_NONE, gst.MESSAGE_ERROR | gst.MESSAGE_EOS)
#		if type(msg) != type(None):
#			break

#	if msg.type == gst.MESSAGE_ERROR:
#		gerror, dbg_msg = msg.parse_error()
#		print "Error         : ", gerror.message
#		print "Debug details : ", dbg_msg

	# Free resources
#	camStream.set_state(gst.STATE_NULL)


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

def handleData():
	global writeLock
	global readLock
	global writeQue
	global readQue

	# Read/write terminal <-> sockets
	while 1:
		if select.select([sys.stdin,],[],[],0.0)[0]:	# If there is input from stdin
			writeLock.acquire()
			writeQue.append(sys.stdin.readline())	# Write it to the write que
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
	start_new_thread(handleData, ())

	print 'Spawned threads.'

	GTK_Main()
	gtk.gdk.threads_init()
	gtk.main()


if __name__ == '__main__':
	main(sys.argv[1:])
