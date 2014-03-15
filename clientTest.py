#!/usr/bin/python2.7

import sys
import socket
import select
import threading
import time
import getopt
import cv2
import pygame
from thread import *
from collections import deque


RHOST = ''			# Get host IP from args
CPORT = 7268			# Control port used by Eugene
VPORT = 7269			# Video port


def rxVideo(PORT):
	screen = pygame.display.set_mode((320,240))

	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	except socket.error, msg:
		print "Failed to create rxSocket, error code: " + str(msg[0]) + " Error message: " + msg[1]
		sys.exit(2)

	s.bind(('', PORT))
	s.listen(1)

	while True:
		conn, addr = s.accept()

		msg = []

		while True:
			d = conn.recv(1024*1024)
			if not d: break
			else: msg.append(d)

		tmp = ''.join(msg)
		img = pygame.image.fromstring(tmp, (320,240), "RGB")

		screen.blit(img, (0,0))
		pygame.display.update()



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

	rxVideo(VPORT)


if __name__ == '__main__':
	main(sys.argv[1:])
