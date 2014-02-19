import sys, socket, select, threading, time, getopt
from thread import *
from collections import deque


RHOST = ''			# Get host IP from args
PORT  = 7268			# Port used by Eugene

readQue  = deque()		# Que for data read from the socket
writeQue = deque()		# Que for data to be sent through the socket

readLock  = threading.Lock();	# Lock for readQue
writeLock = threading.Lock();	# Lock for writeQue


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

	# Set up connections and spawn threads to do socket read and write.
	try:
		conn1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		conn2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	except socket.error, msg:
		print 'Failed to create socket. Error code: ' + str(msg[0]) + ' Error message: ' + msg[1]
		sys.exit(2)

	print 'Sockets created.'

	conn1.connect((RHOST, PORT))
	conn2.connect((RHOST, PORT))

	print 'Sockets connected to host.'

	start_new_thread(sendData, (conn1,))
	start_new_thread(receiveData, (conn2,))

	print 'Spawned threads.'

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

if __name__ == '__main__':
	main(sys.argv[1:])