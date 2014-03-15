#!/usr/bin/python2.7

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst

#GObject.threads_init()
Gst.init(None)

HOST = '192.168.1.107'
PORT = '5000'

# Set up the pipeline
pipeline  = 'v4l2src device=/dev/video0 ! video/x-raw, width=640, height=480, framerate=15/1 ! queue'
pipeline += ' ! videoconvert ! omxh264enc ! rtph264pay pt=96 ! udpsink host=' + HOST + ' port=' + PORT

camStream = Gst.parse_launch(pipeline)

camStream.set_state(Gst.State.PLAYING)

# problem with python wrapper's timed_pop_filtered not excepting GST_CLOCK_TIME_NONE
# fix by redefining it from -1 to max time ammount 4294967295
GST_CLOCK_TIME_NONE = 4294967295

# Wait until error or EOS
bus = camStream.get_bus()

while True:
	msg = bus.timed_pop_filtered(GST_CLOCK_TIME_NONE, Gst.MessageType.ERROR | Gst.MessageType.EOS)
	if type(msg) != type(None):
		break

if msg.type == Gst.MessageType.ERROR:
	gerror, dbg_msg = msg.parse_error()
	print "Error         : ", gerror.message
	print "Debug details : ", dbg_msg

# Free resources
camStream.set_state(Gst.State.NULL)
