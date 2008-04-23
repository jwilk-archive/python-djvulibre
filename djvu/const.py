# encoding=UTF-8
# Copyright © 2008 Jakub Wilk <ubanus@users.sf.net>

'''DjVuLibre bindings: various constants.'''

import djvu.sexpr

EMPTY_LIST = djvu.sexpr.Expression([])
EMPTY_OUTLINE = djvu.sexpr.Expression([djvu.sexpr.Symbol('bookmarks')])

METADATA_BIBTEX_KEYS = frozenset(map(djvu.sexpr.Symbol, '''\
address
author
booktitle
chapter
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
year'''.split()))
# Retrieved from <http://nwalsh.com/tex/texhelp/bibtx-7.html>

METADATA_PDFINFO_KEYS = frozenset(map(djvu.sexpr.Symbol, '''\
Author
CreationDate
Creator
Keywords
ModDate
Producer
Subject
Title
Trapped'''.split()))
# Retrived from the PDF specification

METADATA_KEYS = METADATA_BIBTEX_KEYS | METADATA_PDFINFO_KEYS

class TextZoneType(djvu.sexpr.Symbol):

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
	
	def __cmp__(self, other):
		if self == other:
			return 0
		if not isinstance(other, TextZoneType):
			raise TypeError('cannot compare a text zone type with other object')
		return cmp(self.__rank, other.__rank)
	
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

MAPAREA_SHAPE_RECTANGLE = djvu.sexpr.Symbol('rect')
MAPAREA_SHAPE_OVAL      = djvu.sexpr.Symbol('oval')
MAPAREA_SHAPE_POLYGON   = djvu.sexpr.Symbol('poly')
MAPAREA_SHAPE_LINE      = djvu.sexpr.Symbol('line')
MAPAREA_SHAPE_TEXT      = djvu.sexpr.Symbol('text')

MAPAREA_BORDER_NONE        = djvu.sexpr.Symbol('none')
MAPAREA_BORDER_XOR         = djvu.sexpr.Symbol('xor')
MAPAREA_BORDER_SOLID_COLOR = djvu.sexpr.Symbol('border')

MAPAREA_BORDER_SHADOW_IN  = djvu.sexpr.Symbol('shadow_in')
MAPAREA_BORDER_SHADOW_OUT = djvu.sexpr.Symbol('shadow_out')
MAPAREA_BORDER_ETCHED_IN  = djvu.sexpr.Symbol('shadow_ein')
MAPAREA_BORDER_ETCHED_OUT = djvu.sexpr.Symbol('shadow_eout')
MAPAREA_SHADOW_BORDERS = (MAPAREA_BORDER_SHADOW_IN, MAPAREA_BORDER_SHADOW_OUT, MAPAREA_BORDER_ETCHED_IN, MAPAREA_BORDER_ETCHED_OUT)

MAPAREA_BORDER_ALWAYS_VISIBLE = djvu.sexpr.Symbol('border_avis')

MAPAREA_HREF = djvu.sexpr.Symbol('href')

ANNOTATION_BACKGROUND = djvu.sexpr.Symbol('background')
ANNOTATION_ZOOM       = djvu.sexpr.Symbol('zoom')
ANNOTATION_MODE       = djvu.sexpr.Symbol('mode')
ANNOTATION_ALIGN      = djvu.sexpr.Symbol('align')
ANNOTATION_MAPAREA    = djvu.sexpr.Symbol('maparea')
ANNOTATION_METADATA   = djvu.sexpr.Symbol('metadata')

# vim:ts=4 sw=4 noet
