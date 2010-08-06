# encoding=UTF-8
# Copyright © 2008, 2009 Jakub Wilk <jwilk@jwilk.net>
#
# This package is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This package is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

'''DjVuLibre bindings: various constants.'''

import djvu.sexpr

EMPTY_LIST = djvu.sexpr.Expression([])
EMPTY_OUTLINE = djvu.sexpr.Expression([djvu.sexpr.Symbol('bookmarks')])

METADATA_BIBTEX_KEYS = frozenset(djvu.sexpr.Symbol(x) for x in '''\
address
annote
author
booktitle
chapter
crossref
edition
editor
howpublished
institution
journal
key
month
note
number
organization
pages
publisher
school
series
title
type
volume
year'''.split())
# Retrieved from <http://www.ctan.org/get/biblio/bibtex/contrib/doc/btxdoc.pdf>

METADATA_PDFINFO_KEYS = frozenset(djvu.sexpr.Symbol(x) for x in '''\
Author
CreationDate
Creator
Keywords
ModDate
Producer
Subject
Title
Trapped'''.split())
# Retrived from the PDF specification

METADATA_KEYS = METADATA_BIBTEX_KEYS | METADATA_PDFINFO_KEYS

class TextZoneType(djvu.sexpr.Symbol):

    '''
    A type of a text zone. You can compare text zone types with the < operator.

    To create objects of this class, use the get_text_zone_type() function.
    '''

    __cache = {}

    @classmethod
    def from_symbol(cls, symbol):
        return cls.__cache[symbol]

    def __new__(cls, value, rank):
        self = djvu.sexpr.Symbol.__new__(cls, value)
        TextZoneType.__cache[self] = self
        return self

    def __init__(self, value, rank):
        self.__rank = rank

    def __lt__(self, other):
        if not isinstance(other, TextZoneType):
            raise TypeError('cannot compare text zone type with other object')
        return self.__rank < other.__rank

    def __le__(self, other):
        if not isinstance(other, TextZoneType):
            raise TypeError('cannot compare text zone type with other object')
        return self.__rank <= other.__rank

    def __gt__(self, other):
        if not isinstance(other, TextZoneType):
            raise TypeError('cannot compare text zone type with other object')
        return self.__rank > other.__rank

    def __ge__(self, other):
        if not isinstance(other, TextZoneType):
            raise TypeError('cannot compare text zone type with other object')
        return self.__rank >= other.__rank

    def __repr__(self):
        return '<%s.%s: %s>' % (self.__module__, self.__class__.__name__, self)

TEXT_ZONE_PAGE = TextZoneType('page', 7)
TEXT_ZONE_COLUMN = TextZoneType('column', 6)
TEXT_ZONE_REGION = TextZoneType('region', 5)
TEXT_ZONE_PARAGRAPH = TextZoneType('para', 4)
TEXT_ZONE_LINE = TextZoneType('line', 3)
TEXT_ZONE_WORD = TextZoneType('word', 2)
TEXT_ZONE_CHARACTER = TextZoneType('char', 1)

def get_text_zone_type(symbol):
    return TextZoneType.from_symbol(symbol)

TEXT_ZONE_SEPARATORS = \
{
    TEXT_ZONE_PAGE:      '\f',   # Form Feed (FF)
    TEXT_ZONE_COLUMN:    '\v',   # Vertical tab (VT, LINE TABULATION)
    TEXT_ZONE_REGION:    '\035', # Group Separator (GS, INFORMATION SEPARATOR THREE)
    TEXT_ZONE_PARAGRAPH: '\037', # Unit Separator (US, INFORMATION SEPARATOR ONE)
    TEXT_ZONE_LINE:      '\n',   # Line Feed (LF)
    TEXT_ZONE_WORD:      ' ',    # space
    TEXT_ZONE_CHARACTER: ''
}

# 8.3.4.2 Maparea (overprinted annotations)
ANNOTATION_MAPAREA    = djvu.sexpr.Symbol('maparea')

# 8.3.4.2 Maparea (overprinted annotations):
MAPAREA_SHAPE_RECTANGLE = djvu.sexpr.Symbol('rect')
MAPAREA_SHAPE_OVAL      = djvu.sexpr.Symbol('oval')
MAPAREA_SHAPE_POLYGON   = djvu.sexpr.Symbol('poly')
MAPAREA_SHAPE_LINE      = djvu.sexpr.Symbol('line')
MAPAREA_SHAPE_TEXT      = djvu.sexpr.Symbol('text')

MAPAREA_URI = MAPAREA_URL = djvu.sexpr.Symbol('url')

# 8.3.4.2.3.1.1 Border type:
MAPAREA_BORDER_NONE        = djvu.sexpr.Symbol('none')
MAPAREA_BORDER_XOR         = djvu.sexpr.Symbol('xor')
MAPAREA_BORDER_SOLID_COLOR = djvu.sexpr.Symbol('border')

# 8.3.4.2.3.1.1 Border type:
MAPAREA_BORDER_SHADOW_IN  = djvu.sexpr.Symbol('shadow_in')
MAPAREA_BORDER_SHADOW_OUT = djvu.sexpr.Symbol('shadow_out')
MAPAREA_BORDER_ETCHED_IN  = djvu.sexpr.Symbol('shadow_ein')
MAPAREA_BORDER_ETCHED_OUT = djvu.sexpr.Symbol('shadow_eout')
MAPAREA_SHADOW_BORDERS = (MAPAREA_BORDER_SHADOW_IN, MAPAREA_BORDER_SHADOW_OUT, MAPAREA_BORDER_ETCHED_IN, MAPAREA_BORDER_ETCHED_OUT)
MAPAREA_SHADOW_BORDER_MIN_WIDTH = 1
MAPAREA_SHADOW_BORDER_MAX_WIDTH = 32

# 8.3.4.2.3.1.2 Border always visible
MAPAREA_BORDER_ALWAYS_VISIBLE = djvu.sexpr.Symbol('border_avis')

# 8.3.4.2.3.1.3 Highlight color and opacity:
MAPAREA_HIGHLIGHT_COLOR = djvu.sexpr.Symbol('hilite')
MAPAREA_OPACITY         = djvu.sexpr.Symbol('opacity')
MAPAREA_OPACITY_MIN     = 0
MAPAREA_OPACITY_DEFAULT = 50
MAPAREA_OPACITY_MAX     = 100

# 8.3.4.2.3.1.4 Line and Text parameters:
MAPAREA_ARROW            = djvu.sexpr.Symbol('arrow')
MAPAREA_LINE_WIDTH       = djvu.sexpr.Symbol('width')
MAPAREA_LINE_COLOR       = djvu.sexpr.Symbol('lineclr')
MAPAREA_LINE_MIN_WIDTH = 1
MAPAREA_LINE_COLOR_DEFAULT = '#000000'

# 8.3.4.2.3.1.4 Line and Text parameters:
MAPAREA_BACKGROUND_COLOR = djvu.sexpr.Symbol('backclr')
MAPAREA_TEXT_COLOR       = djvu.sexpr.Symbol('textclr')
MAPAREA_PUSHPIN          = djvu.sexpr.Symbol('pushpin')
MAPAREA_TEXT_COLOR_DEFAULT = '#000000'

# 8.3.4.1 Initial Document View :
ANNOTATION_BACKGROUND = djvu.sexpr.Symbol('background')  # 8.3.4.1.1 Background Color
ANNOTATION_ZOOM       = djvu.sexpr.Symbol('zoom') # 8.3.4.1.2 Initial Zoom
ANNOTATION_MODE       = djvu.sexpr.Symbol('mode') # 8.3.4.1.3 Initial Display level
ANNOTATION_ALIGN      = djvu.sexpr.Symbol('align') # 8.3.4.1.4 Alignment

# djvuchanges.txt, sections "Metadata Annotations" and "Document Annotations and Metadata":
ANNOTATION_METADATA   = djvu.sexpr.Symbol('metadata')

# 8.3.4.3 Printed headers and footers:
ANNOTATION_PRINTED_HEADER = djvu.sexpr.Symbol('phead')
ANNOTATION_PRINTED_FOOTER = djvu.sexpr.Symbol('pfoot')
PRINTER_HEADER_ALIGN_LEFT   = PRINTED_FOOTER_ALIGN_LEFT   = djvu.sexpr.Symbol('left')
PRINTER_HEADER_ALIGN_CENTER = PRINTED_FOOTER_ALIGN_CENTER = djvu.sexpr.Symbol('center')
PRINTER_HEADER_ALIGN_RIGHT  = PRINTED_FOOTER_ALIGN_RIGHT  = djvu.sexpr.Symbol('right')

# vim:ts=4 sw=4 et
