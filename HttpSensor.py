import PowerControllerSensor
import urlparse
import httplib
import base64
from lxml import etree
import StringIO
import time
import logging

class HttpSensor(PowerControllerSensor.PowerControllerSensor):
    	def __init__(self, url, xpath=None, user=None, password=None, interval=2):
		PowerControllerSensor.PowerControllerSensor.__init__(self)
		self.url = url
		self.headers = {}
		self.poll_interval = interval
		self.xpath = xpath

		parsed_url = urlparse.urlparse(url)
		hostname = parsed_url.hostname
		self.headers['Host'] = parsed_url.netloc
		port = parsed_url.port
		if port == None: port = httplib.HTTP_PORT

		user = user
		if user == None: user = parsed_url.username
		password = password
		if password == None: password = parsed_url.password
		if user != None and password != None:
			self.headers['Authorization'] = "Basic " + base64.b64encode(user + ":" + password)

		self.url_used = url[url.find(parsed_url.netloc) + len(parsed_url.netloc):]
		self.http_connection = httplib.HTTPConnection(hostname, port)
		self.send_query()

	def send_query(self):
		self.http_connection.request("GET",  self.url_used, headers=self.headers)
		response = self.http_connection.getresponse()
		content = response.read()
		logging.debug("HTTP response content: %s", content)
		if (self.xpath != None):
			parser = etree.HTMLParser()
			tree = etree.fromstring(content,parser)
			logging.debug("normalized tree: %s", etree.tostring(tree))
			r = tree.xpath(self.xpath)
			logging.debug("xpath result: %s", r)
			#logging.debug("xpath result content: %s", r[0].text)
			exit
		
		

	def get_state(self):
		return set()
		
	def get_selectable_fds(self): 
		return []
	
	def get_poll_interval(self):
		return self.poll_interval

	def do_poll(self):
		self.send_query()
	
	def do_read(self):
		pass

