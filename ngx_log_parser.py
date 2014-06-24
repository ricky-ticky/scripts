#!/usr/bin/python

import re
from datetime import datetime
import pickle
import sys
import os

#config
#log = "/var/log/nginx/invitro.ru.access.log"
log = "/tmp/invitro.ru.access.log"
mark = "/var/tmp/log_mark"


class Initializer(object):
	def __init__(self, log, mark):
		self.log = log
		self.mark = mark
		self.position = 0
		self.full_scan = 0
		self.now = datetime.now() 
		
	def __float__(self):
		return self.avg
	
	def run(self):
		try:
			#read last_state_mark
			markfile = open(self.mark, "r")
			self.position = pickle.load(markfile)
		except:
			#print "No markfile fount. Go to the end of file"
			#self.search_right_place()
			self.go_to_the_end()
			self.avg = -1
		#self.avg = self.get_log_lines()
		self.get_log_lines()
		self.save_position()
	
	def search_right_place(self):
		"""Seach for actual place in log file"""
		if self.full_scan:
			#print "can't find current time in log"
			sys.exit(1)
		self.full_scan = 1
		try:
			logfile = open(self.log, "r")
		except:
			#print "error opening log file"
			sys.exit(1)
		while 1:
			#read line, get timestamp, compare with current
			line = logfile.readline()
			if line: #TODO: check if a string a valid apache-format logline
				if self.check_if_line_has_same_minute(line):
					self.position = logfile.tell()
					logfile.close()
					break
				else:
					pass
			else:
				logfile.close()
				break
		if not self.position:
			#print "can't find current time in log"
			sys.exit(1)
	def go_to_the_end(self):
		"""Go to the end of logfile"""
		logfile = open(self.log,"r")
		logfile.seek(-1,os.SEEK_END)
		self.position = logfile.tell()
		logfile.close()
		self.save_position()
		
	def search_from_markpoint(self):
		"""Search for actual place in logfile from markpoint"""
		pass
	
	def grab_time(self, line):
		"""distinguish timestamp from log line"""
		try:
			stamp = line.split()[4][1:]
			timestamp = datetime.strptime(stamp, "%d/%b/%Y:%H:%M:%S")
		except:
			return False
		return timestamp
	
	def check_if_line_has_same_minute(self, line):
		"""Checks that log line have timestamp not less than delta"""
		line_timestamp = self.grab_time(line)
		if not line_timestamp:
			return False
		delta = self.now - line_timestamp
		if delta.seconds <= 60:
			return True
		else:
			return False
	
	def get_log_lines(self):
		"""Find out exactly what lines of log should we parse"""
		#open log file
		try:
			logfile = open(self.log, "r")
			logfile.seek(self.position)
		except:
			#print "error openning/seeking logfile"
			sys.exit(1)
		lines = logfile.readlines()
		self.position = logfile.tell()
		if not lines:
			self.save_position()
			self.avg = -1
		else:
			if self.check_if_line_has_same_minute(lines[0]):
				self.avg=self.parse(lines)
			else:
				#self.search_right_place()
				self.avg = -1
				self.go_to_the_end()
				#self.get_log_lines()

	def parse(self, lines):
		"""Return average response time as float or False"""
		regex = re.compile(r".* \[.*\] \".*\" (?P<http_code>\d*) \d* \".*\" \".*\" \[ [0-9\.]*:\d\d (?P<backend_resp_time>[0-9.]*) \] .* \".*\" cache:(?P<cache_hit>(-|HIT)) .*")
		sum_resp_time = 0.0
		mutch_counter = 0
		for l in lines:
			a = regex.search(l)
			if a:
				cache = str(a.group("cache_hit"))
				resp_time = float(a.group("backend_resp_time"))
				http_code = int(a.group("http_code"))
				if cache is not 'HIT' and http_code == 200 and resp_time > 0:
					mutch_counter += 1
					sum_resp_time += resp_time
		if mutch_counter is not 0:
			return sum_resp_time/mutch_counter
		else:
			return False
	
	def save_position(self):
		"""Seves current position of logfile in markfile"""
		try:
			markfile = open(mark, "w")
			pickle.dump(self.position, markfile)
			markfile.close()
		except:
			print "can't write mark file"
			pass

if __name__=="__main__":
	chewy = Initializer(log, mark)
	chewy.run()
	print chewy.avg

#TODO: more clever search - not from the beginning. Maybe just faster search from beginning.