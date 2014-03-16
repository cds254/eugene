#!/usr/bin/env python
# Currently Broken

import sys
import os
import time
import pygame
import gobject
import pygst
pygst.require("0.10")
import gst

gobject.threads_init()

vidsize = ''
img_sfc = ""
img_buffer = ""

def setupStream():
	# Set up the gstreamer pipeline
	global vidsize
	global img_sfc
	global img_buffer


	player = gst.Pipeline("player")

	_VIDEO_CAPS = ','.join([
		'video/x-raw-rgb',
		'red_mask=(int)0xff0000',
		'green_mask=(int)0x00ff00',
		'blue_mask=(int)0x0000ff'
		])

	caps = gst.Caps(_VIDEO_CAPS)

	source = gst.element_factory_make("videotestsrc", "source")

	sink = gst.element_factory_make('appsink', 'videosink')
	sink.set_property('caps', caps)
	sink.set_property('emit-signals', True)
	sink.connect('new-buffer', __handle_frame)

	player.add(source, sink)
	gst.element_link_many(source, sink)


	bus = player.get_bus()
	bus.add_signal_watch()
	bus.enable_sync_message_emission()
	bus.connect("message", on_message)

	# Pause the stream to get size info
	player.set_state(gst.STATE_PAUSED)

	# Once stream is negotiated, get info
	if player.get_state(gst.CLOCK_TIME_NONE)[0] == gst.STATE_CHANGE_SUCCESS:
		pads = sink.pads()
		for pad in pads:
			caps = pad.get_negotiated_caps()[0]
			vidsize = caps['width'], caps['height']
	else:
		raise exceptions.runtime_error("Failed to retrieve video size")

	
	# Create a pygame surface with a 24 bit color depth and flags for RGB format (Red = 0x0000FF, Green = 0x00FF00, Blue = 0xFF0000)
	img_sfc = pygame.Surface(vidsize, pygame.SWSURFACE, 24, (255, 65280, 16711680, 0))
	img_buffer = img_sfc.get_buffer()

	# Set the stream to active
	player.set_state(gst.STATE_PLAYING)

def on_message(bus, message):
	t = message.type
	if t == gst.MESSAGE_EOS:
		player.set_state(gst.STATE_NULL)
		err, debug = message.parse_error()
		print "Error: %s" % err, debug
		player.set_state(gst.STATE_NULL)


def __handle_frame(appsink):
	# Handle video frames, sending them to pygame
	global vidsize
	global img_sfc
	global img_buffer

	buffer = appsink.emit('pull-buffer')

#	img = pygame.image.frombuffer(buffer.data, vidsize, "RGB")

	print "Vid size: " + str(vidsize)
	print "Expected size: " + str(vidsize[0]*vidsize[1]*3)
	print "Got: " + str(sys.getsizeof(buffer.data))

	img_buffer.write(buffer.data, 0)
	pygame.display.get_surface().blit(img_sfc.copy(), (0,0))

#	screen.blit(img, 0)

	# Swap the buffers
	pygame.display.flip()


pygame.init()
#screen = pygame.display.set_mode((640,480), 0)
setupStream();

while True:
	time.sleep(1)
