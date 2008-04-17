from djvu.const import *
import unittest
import doctest

class TextZonesTest:
	r'''
	>>> zones = (TEXT_ZONE_PAGE, TEXT_ZONE_COLUMN, TEXT_ZONE_REGION, TEXT_ZONE_PARAGRAPH, TEXT_ZONE_LINE, TEXT_ZONE_WORD, TEXT_ZONE_CHARACTER)
	>>> [[cmp(z1, z2) for z1 in zones] for z2 in zones]
	[[0, -1, -1, -1, -1, -1, -1], [1, 0, -1, -1, -1, -1, -1], [1, 1, 0, -1, -1, -1, -1], [1, 1, 1, 0, -1, -1, -1], [1, 1, 1, 1, 0, -1, -1], [1, 1, 1, 1, 1, 0, -1], [1, 1, 1, 1, 1, 1, 0]]
	'''

if __name__ == '__main__':
	import os, sys
	os.chdir(sys.path[0])
	del os, sys
	doctest.testmod(verbose = False)
	doctest.master.summarize(verbose = True)
	print
	unittest.main()
	print; print

# vim:ts=4 sw=4 noet
