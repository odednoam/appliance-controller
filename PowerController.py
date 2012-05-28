import ConfigParser
import inspect
import select
import time
import re
import os
import logging
import string
from optparse import OptionParser

class Device:
	def __init__(self, config, section):
		self.device_name = section
		self.power_on_command = config.get(section, 'power_on_command')
		self.power_off_command = config.get(section, 'power_off_command')
		required_state_str = config.get(section, 'required_state')
		self.required_state = set( re.compile('\s*\\|\s*').split(required_state_str) )
		self.power_state = True # next command will make sure is off
		self.power_off()

	def update_state(self, state):
		if len(state & self.required_state)>0:
			self.power_on()
		else: 
			self.power_off()
	
	def power_on(self):
		if (not self.power_state): 
			logging.info("Powering on %s (command: %s)", self.device_name, self.power_on_command)
			self.power_state = True
			ret = os.system(self.power_on_command)
			logging.debug("return value from executing command: %s", ret)
	
	def power_off(self):
		if (self.power_state): 
			logging.info("Powering off %s (command: %s)", self.device_name, self.power_off_command)
			self.power_state = False
			ret = os.system(self.power_off_command)
			logging.debug("return value from executing command: %s", ret)

def search_file(filename, paths):
   """Given a search path, find file
   """
   file_found = 0
   for path in paths:
      if os.path.exists(os.path.join(path, filename)):
          file_found = 1
          break
   if file_found:
      return os.path.abspath(os.path.join(path, filename))
   else:
      return None

cmdline_parser = OptionParser()
cmdline_parser.add_option("-d", "--debug", action="callback", callback=lambda x,y,z,w:logging.basicConfig(level=logging.DEBUG))
cmdline_parser.add_option("-i", "--info", action="callback", callback=lambda x,y,z,w:logging.basicConfig(level=logging.INFO))
cmdline_parser.parse_args()

config = ConfigParser.RawConfigParser()
config_file = search_file('powercontroller.cfg', ['.', '~/', '/etc/powercontroller'])
logging.info("Loading configuration from %s", config_file)
config.readfp(open(config_file))
sensors = []
devices = []

exit
for section in config.sections():
	if config.has_option(section, 'sensor_module'):
		# This configuration section defines a sensor
		module = __import__(config.get(section, 'sensor_module'), fromlist="")
		sensor_class = getattr(module, config.get(section, 'sensor_class') )
		sensor_ctor = getattr(sensor_class, '__init__')

		ctor_args = inspect.getargspec(sensor_ctor)[0]
		ctor_defaults = inspect.getargspec(sensor_ctor)[3]
		if ctor_defaults == None: ctor_defaults = []

		actual_args = []
		args_remaining = len(ctor_args)
		for arg in ctor_args[1:]:
			args_remaining -= 1
			config_arg = 'sensor_' + arg;
			if (args_remaining <= len(ctor_defaults)) and not config.has_option(section, config_arg):
				actual_args.append(ctor_defaults[-args_remaining])
			else:
				actual_args.append(config.get(section, config_arg))
		sensor = sensor_class(*actual_args)
		logging.info("Instantiated sensor: %s", sensor)
		sensors.append(sensor)
		
	else:
		# This configuration section defines a controller
		devices.append(Device(config, section))


last_poll = time.time()
old_state = set()

while 1:
	fds = {}
	timeout = 0;
	for s in sensors:
		timeout = max(timeout, s.get_poll_interval())
		for fd in s.get_selectable_fds():
			fds[fd] = s

	if (timeout == 0):
		logging.debug("selecting without timeout ")
		selected_fds = select.select(fds.keys(), [], [])[0]
	else:
		logging.debug("selecting with timeout %d", timeout)
		selected_fds = select.select(fds.keys(), [], [], timeout)[0]
	for fd in selected_fds:
		fds[fd].do_read()
	logging.debug("timeout is %d, time since last poll %d", timeout, (time.time() - last_poll))
	if (timeout > 0 and (time.time() - last_poll)*1000 > timeout):
		last_poll = time.time()
		for s in sensors: s.do_poll()

	state = set()
	for s in sensors: state |= s.get_state()
	if state != old_state: 
		for d in devices: d.update_state(state)
	old_state = state
