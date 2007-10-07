from miniexp import *
from os import getpid
import gc

PROC_STATUS = '/proc/%d/status' % getpid()
SCALE = dict(kB = 1024.0)

def mem_info(key = 'VmSize'):
	try:
		file = open(PROC_STATUS)
		for line in file:
			if line.startswith('%(key)s:' % locals()):
				_, value, unit = line.split(None, 3)
				return float(value) * SCALE[unit]
	finally:
		file.close()

STEP = 1 << 17

n = 0
while True:
	print '%.2fM' % mem_info()
	[Expression(4) for i in xrange(STEP)]
	break

# vim:ts=4 sw=4 noet
