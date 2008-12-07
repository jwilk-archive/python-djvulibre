# encoding=UTF-8
# Copyright © 2007, 2008 Jakub Wilk <ubanus@users.sf.net>
#
# This package is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This package is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

from djvu.sexpr import *
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

# vim:ts=4 sw=4 et
