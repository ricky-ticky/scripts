#!/usr/bin/python

import re
from datetime import datetime
import pickle
import sys

#config
log = "/var/log/nginx/invitro.ru.access.log"
mark = "/var/tmp/log_mark"


class Initializer(object):
	def __init__(self, log, pmark):
		self.log = log
		self.mark = mark
		self.position = 0
		self.full_scan = 0
		self.now = datetime.now() 
		try:
		#read last_state_mark
			markfile = open(self.mark, "r")
			self.position = pickle.load(markfile)
		except:
			#print "No markfile fount. Searching right place by timestamp"
			self.search_right_place()
		self.avg = self.get_log_lines()
		self.save_position()
	def __float__(self):
		return self.avg
	
	def search_right_place(self):
		"""Seaching for actual place in log file"""
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
			if line:
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
		delta = self.now - line_timestamp
		if delta.seconds <= 60:
			return True
		else:
			return False
	
	def get_log_lines(self):
		"""Finding out exactly what lines of log should we parse"""
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
		else:
			if self.check_if_line_has_same_minute(lines[0]):
				return self.parse(lines)
			else:
				self.search_right_place()
				self.get_log_lines()

	def parse(self, lines):
		"""Returns average response time as float or False"""
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
		
chewy = Initializer(log, mark)
print chewy.avg

