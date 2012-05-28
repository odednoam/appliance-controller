import socket
import icmplib
import struct
import PowerControllerSensor
import os
import time
import logging

process_id = os.getpid()
BUFSIZE=1500

class PingSensor(PowerControllerSensor.PowerControllerSensor):
    	def __init__(self, addr, interval=1):
		PowerControllerSensor.PowerControllerSensor.__init__(self)
		self.sock = socket.socket(socket.AF_INET,socket.SOCK_RAW,
              		socket.getprotobyname('icmp'))
		self.sock.connect((addr,22))
		self.poll_interval = float(interval)
		self.last_response_time = 0
		self.addr = addr

		## create ping packet 
		self.base_packet = icmplib.Packet((8,0))
		self.seq_num = 0
		self.send_ping()

	def send_ping(self):
		self.seq_num += 1;
		pdata = struct.pack("!HHd",process_id,self.seq_num,time.time())
		
		## send initial packet 
		self.base_packet.data = pdata
		self.sock.send(self.base_packet.packet)

	def get_state(self):
		if (time.time() - self.last_response_time) > self.poll_interval*2:
			return set()
		else:
			return set([self.addr + "_alive"])
		
	def get_selectable_fds(self): 
		return [self.sock.fileno()]
	
	def get_poll_interval(self):
		return self.poll_interval

	def do_poll(self):
		self.send_ping()
	
	def do_read(self):
		## recv packet
		buf = self.sock.recv(BUFSIZE)
		current_time = time.time()
		
		## parse packet; remove IP header first
		r = icmplib.Packet.parse(buf[20:])
		
		## parse ping data
		(ident,seq,timestamp) = struct.unpack("!HHd",r.data)
		
		## calculate rounttrip time
		rtt =  current_time - timestamp
		rtt *= 1000
		logging.debug("%d bytes from %s: id=%s, seq=%u, rtt=%.3f ms" % (len(buf),
			"addr", ident, seq, rtt)
		self.last_response_time = current_time

