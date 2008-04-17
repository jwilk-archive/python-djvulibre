# encoding=UTF-8
# Copyright © 2008 Jakub Wilk <ubanus@users.sf.net>

'''DjVuLibre bindings: various constants.'''

import djvu.decode

METADATA_BIBTEX_KEYS = set(('address', 'author', 'booktitle', 'chapter', 'edition', 'editor', 'howpublished', 'institution', 'journal', 'key', 'month', 'note', 'number', 'organization', 'pages', 'publisher', 'school', 'series', 'title', 'type', 'volume', 'year'))
# Retrieved from <http://nwalsh.com/tex/texhelp/bibtx-7.html>

METADATA_PDFINFO_KEYS = set(('Author', 'CreationDate', 'Creator', 'Keywords', 'ModDate', 'Producer', 'Subject', 'Title', 'Trapped'))
# Retrived from the PDF specification

METADATA_KEYS = METADATA_BIBTEX_KEYS | METADATA_PDFINFO_KEYS

ZONE_SEPARATORS = \
{
	djvu.decode.TEXT_ZONE_PAGE:      '\f',   # Form Feed (FF)
	djvu.decode.TEXT_ZONE_COLUMN:    '\v',   # Vertical tab (VT, LINE TABULATION)
	djvu.decode.TEXT_ZONE_REGION:    '\035', # Group Separator (GS, INFORMATION SEPARATOR THREE)
	djvu.decode.TEXT_ZONE_PARAGRAPH: '\037', # Unit Separator (US, INFORMATION SEPARATOR ONE)
	djvu.decode.TEXT_ZONE_LINE:      '\n',   # Line Feed (LF)
	djvu.decode.TEXT_ZONE_WORD:      ' ',    # space
	djvu.decode.TEXT_ZONE_CHARACTER: ''
}

__all__ = \
(
	'METADATA_BIBTEX_KEYS', 'METADATA_PDFINFO_KEYS', 'METADATA_KEYS',
	'ZONE_SEPARATORS',
)

# vim:ts=4 sw=4 noet
