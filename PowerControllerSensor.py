import socket, string, urllib, select

CRLF = "\r\n"

class PowerControllerSensor:
	def __init__(self):
		self.state = set()

	def get_selectable_fds(self): abstract

	def get_poll_interval(self): 
		return 0

	def do_read(self): abstract
	
	def do_poll(self): pass

	def get_state(self): 
		return self.state;



