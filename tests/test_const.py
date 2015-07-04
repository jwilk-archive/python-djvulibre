# encoding=UTF-8

# Copyright © 2008-2015 Jakub Wilk <jwilk@jwilk.net>
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

from common import *

class test_text_zones():

    zones = [
        TEXT_ZONE_PAGE,
        TEXT_ZONE_COLUMN,
        TEXT_ZONE_REGION,
        TEXT_ZONE_PARAGRAPH,
        TEXT_ZONE_LINE,
        TEXT_ZONE_WORD,
        TEXT_ZONE_CHARACTER
    ]

    def test_type(self):
        for zone in self.zones:
            assert_equal(type(zone), TextZoneType)
            assert_is_instance(zone, Symbol)

    def test_repr(self):
        assert_repr(TEXT_ZONE_PAGE, '<djvu.const.TextZoneType: page>')
        assert_repr(TEXT_ZONE_COLUMN, '<djvu.const.TextZoneType: column>')
        assert_repr(TEXT_ZONE_REGION, '<djvu.const.TextZoneType: region>')
        assert_repr(TEXT_ZONE_PARAGRAPH, '<djvu.const.TextZoneType: para>')
        assert_repr(TEXT_ZONE_LINE, '<djvu.const.TextZoneType: line>')
        assert_repr(TEXT_ZONE_WORD, '<djvu.const.TextZoneType: word>')
        assert_repr(TEXT_ZONE_CHARACTER, '<djvu.const.TextZoneType: char>')

    def test_identity(self):
        assert_is(TEXT_ZONE_PAGE, get_text_zone_type(Symbol('page')))
        assert_is(TEXT_ZONE_COLUMN, get_text_zone_type(Symbol('column')))
        assert_is(TEXT_ZONE_REGION, get_text_zone_type(Symbol('region')))
        assert_is(TEXT_ZONE_PARAGRAPH, get_text_zone_type(Symbol('para')))
        assert_is(TEXT_ZONE_LINE, get_text_zone_type(Symbol('line')))
        assert_is(TEXT_ZONE_WORD, get_text_zone_type(Symbol('word')))
        assert_is(TEXT_ZONE_CHARACTER, get_text_zone_type(Symbol('char')))

    def test_comparison1(self):
        assert_not_equal(TEXT_ZONE_PAGE, '')
        assert_not_equal(TEXT_ZONE_PAGE, 42)
        with assert_raises_str(TypeError, 'cannot compare text zone type with other object'):
            TEXT_ZONE_PAGE < 42
        with assert_raises_str(TypeError, 'cannot compare text zone type with other object'):
            TEXT_ZONE_PAGE <= 42
        with assert_raises_str(TypeError, 'cannot compare text zone type with other object'):
            TEXT_ZONE_PAGE > 42
        with assert_raises_str(TypeError, 'cannot compare text zone type with other object'):
            TEXT_ZONE_PAGE >= 42

    def test_comparison2(self):
        assert_equal(self.zones, sorted(self.zones, reverse=True))
        assert_equal(
            [[cmp(z1, z2) for z1 in self.zones] for z2 in self.zones], [
                [0, -1, -1, -1, -1, -1, -1],
                [+1, 0, -1, -1, -1, -1, -1],
                [+1, +1, 0, -1, -1, -1, -1],
                [+1, +1, +1, 0, -1, -1, -1],
                [+1, +1, +1, +1, 0, -1, -1],
                [+1, +1, +1, +1, +1, 0, -1],
                [+1, +1, +1, +1, +1, +1, 0],
            ]
        )

# vim:ts=4 sts=4 sw=4 et
