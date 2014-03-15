#!/usr/bin/python2.7

import sys
import socket
import threading
import select
import time
import pygame
import pygame.camera
from thread import *

HOST = ''			# symbolic name: all available interfaces
CPORT = 7268			# Control port: RBOT - lololol
VPORT = 7269			# Video port

webcam = ''

def txVideo(IP, PORT):
	global webcam

	time.sleep(1)				# Sleep for a second to wait for the client to get set up

	while True:
		try:
			conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		except socket.error, msg:
			print "Failed to create txSocket, error code: " + str(msg[0]) + " Error message: " + msg[1]
			sys.exit(2)
		
		try:
			conn.connect((IP, PORT))
		except socket.error, e:
			print 'ERROR: ' + str(e) + '\nWaiting for client to reconnect.'

	    	img = webcam.get_image()
		data = pygame.image.tostring(img, "RGB")

		conn.sendall(data)

		conn.close()
		time.sleep(0)


# Main
pygame.init()
pygame.camera.init()

cam_list = pygame.camera.list_cameras()

webcam = pygame.camera.Camera(cam_list[0], (640,480))
webcam.start()

txVideo('192.168.1.107', VPORT)


s.close()
