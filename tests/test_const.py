# encoding=UTF-8

# Copyright © 2008-2015 Jakub Wilk <jwilk@jwilk.net>
#
# This file is part of python-djvulibre.
#
# python-djvulibre is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# python-djvulibre is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.

from djvu.const import (
    TEXT_ZONE_CHARACTER,
    TEXT_ZONE_COLUMN,
    TEXT_ZONE_LINE,
    TEXT_ZONE_PAGE,
    TEXT_ZONE_PARAGRAPH,
    TEXT_ZONE_REGION,
    TEXT_ZONE_WORD,
    TextZoneType,
    get_text_zone_type,
)

from djvu.sexpr import (
    Symbol,
)

from tools import (
    assert_equal,
    assert_is,
    assert_is_instance,
    assert_list_equal,
    assert_not_equal,
    assert_raises_str,
    assert_repr,
    wildcard_import,
    # Python 2/3 compat:
    cmp,
)

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

def test_wildcard_import():
    ns = wildcard_import('djvu.const')
    assert_list_equal(
        sorted(ns.keys()), [
            'ANNOTATION_ALIGN',
            'ANNOTATION_BACKGROUND',
            'ANNOTATION_MAPAREA',
            'ANNOTATION_METADATA',
            'ANNOTATION_MODE',
            'ANNOTATION_PRINTED_FOOTER',
            'ANNOTATION_PRINTED_HEADER',
            'ANNOTATION_ZOOM',
            'EMPTY_LIST',
            'EMPTY_OUTLINE',
            'MAPAREA_ARROW',
            'MAPAREA_BACKGROUND_COLOR',
            'MAPAREA_BORDER_ALWAYS_VISIBLE',
            'MAPAREA_BORDER_ETCHED_IN',
            'MAPAREA_BORDER_ETCHED_OUT',
            'MAPAREA_BORDER_NONE',
            'MAPAREA_BORDER_SHADOW_IN',
            'MAPAREA_BORDER_SHADOW_OUT',
            'MAPAREA_BORDER_SOLID_COLOR',
            'MAPAREA_BORDER_XOR',
            'MAPAREA_HIGHLIGHT_COLOR',
            'MAPAREA_LINE_COLOR',
            'MAPAREA_LINE_COLOR_DEFAULT',
            'MAPAREA_LINE_MIN_WIDTH',
            'MAPAREA_LINE_WIDTH',
            'MAPAREA_OPACITY',
            'MAPAREA_OPACITY_DEFAULT',
            'MAPAREA_OPACITY_MAX',
            'MAPAREA_OPACITY_MIN',
            'MAPAREA_PUSHPIN',
            'MAPAREA_SHADOW_BORDERS',
            'MAPAREA_SHADOW_BORDER_MAX_WIDTH',
            'MAPAREA_SHADOW_BORDER_MIN_WIDTH',
            'MAPAREA_SHAPE_LINE',
            'MAPAREA_SHAPE_OVAL',
            'MAPAREA_SHAPE_POLYGON',
            'MAPAREA_SHAPE_RECTANGLE',
            'MAPAREA_SHAPE_TEXT',
            'MAPAREA_TEXT_COLOR',
            'MAPAREA_TEXT_COLOR_DEFAULT',
            'MAPAREA_URI',
            'MAPAREA_URL',
            'METADATA_BIBTEX_KEYS',
            'METADATA_KEYS',
            'METADATA_PDFINFO_KEYS',
            'PRINTED_FOOTER_ALIGN_CENTER',
            'PRINTED_FOOTER_ALIGN_LEFT',
            'PRINTED_FOOTER_ALIGN_RIGHT',
            'PRINTER_HEADER_ALIGN_CENTER',
            'PRINTER_HEADER_ALIGN_LEFT',
            'PRINTER_HEADER_ALIGN_RIGHT',
            'TEXT_ZONE_CHARACTER',
            'TEXT_ZONE_COLUMN',
            'TEXT_ZONE_LINE',
            'TEXT_ZONE_PAGE',
            'TEXT_ZONE_PARAGRAPH',
            'TEXT_ZONE_REGION',
            'TEXT_ZONE_SEPARATORS',
            'TEXT_ZONE_WORD',
            'TextZoneType',
            'get_text_zone_type'
        ]
    )

# vim:ts=4 sts=4 sw=4 et
