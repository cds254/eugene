import sys, socket, serial, threading, select, time
from thread import *
from collections import deque

HOST = ''			# symbolic name: all available interfaces
PORT = 7268			# PORT: RBOT - lololol

serialRead  = deque()		# Que for writing to serial.
serialWrite = deque()		# Que for reading from serial.

readLock  = threading.Lock();	# Lock for serialRead.
writeLock = threading.Lock();	# Lock for serialWrite.


# Function for handling data recieving.
def receiveData(conn):
	# keep func/thread alive
	while 1:
		data = conn.recv(1)			# Recieve a byte at a time from the client
		if data:				# If no data, loop again
			writeLock.acquire()
			serialWrite.append(data)	# Otherwise, write byte to the write que
			writeLock.release()

		time.sleep(0);

	#came out of loop 
	conn.close()


# Function for data transmittion.
def transmitData(conn):
	while 1:
		readLock.acquire()
		if len(serialRead) > 0:				# If there is data to be sent
			conn.sendall(serialRead.popleft())	# send it
		readLock.release()

		time.sleep(0);


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
	s.bind((HOST, PORT))
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

	data = conn.recv(1024)

	# Start thread to handle communication
	if data == 'T':		# Host is transmitting on this socket
		start_new_thread(receiveData, (conn,))
	elif data == 'R': 	# Host is receiving on this socket
		start_new_thread(transmitData, (conn,))
	else:			# lolwat?
		conn.close()

s.close()
