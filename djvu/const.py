# encoding=UTF-8
# Copyright © 2008 Jakub Wilk <ubanus@users.sf.net>

'''DjVuLibre bindings: various constants.'''

import djvu.sexpr

METADATA_BIBTEX_KEYS = set(('address', 'author', 'booktitle', 'chapter', 'edition', 'editor', 'howpublished', 'institution', 'journal', 'key', 'month', 'note', 'number', 'organization', 'pages', 'publisher', 'school', 'series', 'title', 'type', 'volume', 'year'))
# Retrieved from <http://nwalsh.com/tex/texhelp/bibtx-7.html>

METADATA_PDFINFO_KEYS = set(('Author', 'CreationDate', 'Creator', 'Keywords', 'ModDate', 'Producer', 'Subject', 'Title', 'Trapped'))
# Retrived from the PDF specification

METADATA_KEYS = METADATA_BIBTEX_KEYS | METADATA_PDFINFO_KEYS

class ZoneType(djvu.sexpr.Symbol):

	__cache = {}

	@classmethod
	def from_symbol(cls, symbol):
		return cls.__cache[symbol]

	def __new__(cls, value, rank):
		self = djvu.sexpr.Symbol.__new__(cls, value)
		ZoneType.__cache[self] = self
		return self

	def __init__(self, value, rank):
		self.__rank = rank
	
	def __cmp__(self, other):
		if self == other:
			return 0
		if not isinstance(other, ZoneType):
			return NotImplemented
		return cmp(self.__rank, other.__rank)
	
	def __repr__(self):
		return '<%s.%s: %s>' % (self.__module__, self.__class__.__name__, self)

TEXT_ZONE_PAGE = ZoneType('page', 7)
TEXT_ZONE_COLUMN = ZoneType('column', 6)
TEXT_ZONE_REGION = ZoneType('region', 5)
TEXT_ZONE_PARAGRAPH = ZoneType('para', 4)
TEXT_ZONE_LINE = ZoneType('line', 3)
TEXT_ZONE_WORD = ZoneType('word', 2)
TEXT_ZONE_CHARACTER = ZoneType('char', 1)

def get_zone_from_symbol(symbol):
	return ZoneType.from_symbol(symbol)

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

__all__ = \
(
	'METADATA_BIBTEX_KEYS', 'METADATA_PDFINFO_KEYS', 'METADATA_KEYS',
	'TEXT_ZONE_SEPARATORS',
	'TEXT_ZONE_PAGE', 'TEXT_ZONE_COLUMN', 'TEXT_ZONE_REGION', 'TEXT_ZONE_PARAGRAPH', 'TEXT_ZONE_LINE', 'TEXT_ZONE_WORD', 'TEXT_ZONE_CHARACTER',
	'get_zone_from_symbol'
)

# vim:ts=4 sw=4 noet
