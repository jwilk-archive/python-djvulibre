# encoding=UTF-8

# Copyright © 2007-2015 Jakub Wilk <jwilk@jwilk.net>
#
# This package is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This package is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

from __future__ import division

if __name__ != '__main__':
    raise ImportError('This module is not intended for import')

import djvu.sexpr
import os

PROC_STATUS = '/proc/{pid}/status'.format(pid=os.getpid())
SCALE = dict(kB=1024)

def mem_info(key='VmSize'):
    try:
        file = open(PROC_STATUS)
        for line in file:
            if line.startswith('{key}:'.format(key=key)):
                _, value, unit = line.split(None, 3)
                return int(value) * SCALE[unit]
    finally:
        file.close()

STEP = 1 << 17

try:
    range = xrange
except NameError:
    pass

n = 0
while True:
    mb = mem_info() / (1 << 20)
    print('{mb:.2f}M'.format(mb=mb))
    [djvu.sexpr.Expression(4) for i in range(STEP)]

# vim:ts=4 sw=4 et
