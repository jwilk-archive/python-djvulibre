# encoding=UTF-8
# Copyright © 2008 Jakub Wilk <ubanus@users.sf.net>
#
# This package is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This package is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

from djvu.const import *
from djvu.sexpr import *
import unittest
import doctest

class TextZonesTest:
    r'''
    >>> TEXT_ZONE_PAGE == ''
    False
    >>> TEXT_ZONE_PAGE == 42
    False
    >>> TEXT_ZONE_PAGE < 42
    Traceback (most recent call last):
    ...
    TypeError: cannot compare text zone type with other object


    >>> TEXT_ZONE_PAGE
    <djvu.const.TextZoneType: page>
    >>> TEXT_ZONE_PAGE is get_text_zone_type(Symbol('page'))
    True
    >>> TEXT_ZONE_COLUMN
    <djvu.const.TextZoneType: column>
    >>> TEXT_ZONE_COLUMN is get_text_zone_type(Symbol('column'))
    True
    >>> TEXT_ZONE_REGION
    <djvu.const.TextZoneType: region>
    >>> TEXT_ZONE_REGION is get_text_zone_type(Symbol('region'))
    True
    >>> TEXT_ZONE_PARAGRAPH
    <djvu.const.TextZoneType: para>
    >>> TEXT_ZONE_PARAGRAPH is get_text_zone_type(Symbol('para'))
    True
    >>> TEXT_ZONE_LINE
    <djvu.const.TextZoneType: line>
    >>> TEXT_ZONE_LINE is get_text_zone_type(Symbol('line'))
    True
    >>> TEXT_ZONE_WORD
    <djvu.const.TextZoneType: word>
    >>> TEXT_ZONE_WORD is get_text_zone_type(Symbol('word'))
    True
    >>> TEXT_ZONE_CHARACTER
    <djvu.const.TextZoneType: char>
    >>> TEXT_ZONE_CHARACTER is get_text_zone_type(Symbol('char'))
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

# vim:ts=4 sw=4 et
