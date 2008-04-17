from djvu.const import *
from djvu.sexpr import *
import unittest
import doctest

class TextZonesTest:
	r'''
	>>> TEXT_ZONE_PAGE
	<djvu.const.ZoneType: page>
	>>> TEXT_ZONE_PAGE is get_zone_from_symbol(Symbol('page'))
	True
	>>> TEXT_ZONE_COLUMN
	<djvu.const.ZoneType: column>
	>>> TEXT_ZONE_COLUMN is get_zone_from_symbol(Symbol('column'))
	True
	>>> TEXT_ZONE_REGION
	<djvu.const.ZoneType: region>
	>>> TEXT_ZONE_REGION is get_zone_from_symbol(Symbol('region'))
	True
	>>> TEXT_ZONE_PARAGRAPH
	<djvu.const.ZoneType: para>
	>>> TEXT_ZONE_PARAGRAPH is get_zone_from_symbol(Symbol('para'))
	True
	>>> TEXT_ZONE_LINE
	<djvu.const.ZoneType: line>
	>>> TEXT_ZONE_LINE is get_zone_from_symbol(Symbol('line'))
	True
	>>> TEXT_ZONE_WORD
	<djvu.const.ZoneType: word>
	>>> TEXT_ZONE_WORD is get_zone_from_symbol(Symbol('word'))
	True
	>>> TEXT_ZONE_CHARACTER
	<djvu.const.ZoneType: char>
	>>> TEXT_ZONE_CHARACTER is get_zone_from_symbol(Symbol('char'))
	True
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
