import socket, string, urllib, select, PowerControllerSensor

CRLF = "\r\n"

class VortexBoxSensor(PowerControllerSensor.PowerControllerSensor):
    	def __init__(self, host, port):
		PowerControllerSensor.PowerControllerSensor.__init__(self)
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.connect((host, int(port)))
		self.file = self.sock.makefile("rb") # buffered

		self.players = {}
		count = self.send_command("player count ?")
		for i in range(0, int(count)):
			id = self.send_command("player id " + str(i) + " ?")
			name = self.send_command("player name " + str(i) + " ?")
			mode = self.send_command(id + " mode ?")
			self.state.add(id + "_" + mode)
			power = self.send_command(id + " power ?")
			if power: self.state.add(id + "_power")
			self.players[id] = {"name":name, "mode":mode, "power":power}
			#print "Player [" + id + "] name [" + name + "] mode [" + mode + "]"
		self.send_command("subscribe play,pause,stop,power")

		
	def get_selectable_fds(self): 
		return [self.sock.fileno()]

	def do_read(self):
		updateline = self.read_line()
		#print "State before", self.state
		if len(updateline) == 2:
			self.state.remove(updateline[0] + "_" + self.players[updateline[0]]["mode"])
			self.players[updateline[0]]["mode"] = updateline[1]
			self.state.add(updateline[0] + "_" + self.players[updateline[0]]["mode"])
		elif len(updateline) == 3:
			self.players[updateline[0]][updateline[1]] = updateline[2]
			if int(updateline[2]):
				self.state.add(updateline[0] + "_" + updateline[1])
			else:
				self.state.remove(updateline[0] + "_" + updateline[1])
		#print self.state
		
	def read_line(self):
		s = self.file.readline()
		if not s:
			raise EOFError
		if s[-2:] == CRLF:
			s = s[:-2]
		elif s[-1:] in CRLF:
			s = s[:-1]
		ret = []
		for t in s.split(" "):
			if (t != ""): ret.append(urllib.unquote(t))
		return ret
			
			
	def send_command(self, line):
		self.sock.send(line + CRLF) # unbuffered write
		s = self.file.readline()
		if not s:
			raise EOFError
		if s[-2:] == CRLF:
			s = s[:-2]
		elif s[-1:] in CRLF:
			s = s[:-1]
		if line[-1] == '?':
			tokens = s.split(" ")
			return urllib.unquote(tokens[-1])


