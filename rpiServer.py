import sys, socket, serial
from thread import *

HOST = ''	# symbolic name: all available interfaces
PORT = 7268	# PORT: RBOT - lololol

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print 'Socket created'

try:
	s.bind((HOST, PORT))
except socket.error, msg:
	print 'Bind failed. Error Code: ' + str(msg[0]) + ' Message ' + msg[1]
	sys.exit(2)

print 'Socket bind complete'

# put socket in listening mode
s.listen(2)
print 'Socket now listening.'

# Create a thread to handel the serial connection
start_new_thread(serialHandler)

# Keep accepting connections
while 1:
	# wait to accept a connection - blocking call
	conn, addr = s.accept()

	# display client information
	print 'Connected with ' + addr[0] + ':' + str(addr[1])

	data = conn.recv(1024)

	# Start thread to handle communication
	if data == 'T':		# Host is transmitting on this socket
		start_new_thread(receiveData, (conn,))
	elif data == 'R': 	# Host is receiving on this socket
		start_new_thread(transmitData, (conn,))
	else:			# lolwat?
		conn.close()

s.close()


# Function for handling data recieving.
def receiveData(conn):
	# keep func/thread alive
	while 1:
		# Receive from client
		data = conn.recv(1024)
		if not data:
			break

		conn.sendall(reply)

	#came out of loop 
	conn.close()

# Function for data transmitting.
def transmitData(conn):
	asdfasdf;

def serialHandler():
	asdfasdf;
