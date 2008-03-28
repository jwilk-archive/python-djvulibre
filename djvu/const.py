# encoding=UTF-8
# Copyright © 2008 Jakub Wilk <ubanus@users.sf.net>

'''DjVuLibre bindings: various constants.'''

METADATA_BIBTEX_KEYS = set(('address', 'author', 'booktitle', 'chapter', 'edition', 'editor', 'howpublished', 'institution', 'journal', 'key', 'month', 'note', 'number', 'organization', 'pages', 'publisher', 'school', 'series', 'title', 'type', 'volume', 'year'))
# Retrieved from <http://nwalsh.com/tex/texhelp/bibtx-7.html>

METADATA_PDFINFO_KEYS = set(('Author', 'CreationDate', 'Creator', 'Keywords', 'ModDate' 'Producer', 'Subject', 'Title', 'Trapped'))
# Retrived from the PDF specification

METADATA_KEYS = METADATA_BIBTEX_KEYS | METADATA_PDFINFO_KEYS

# vim:ts=4 sw=4 noet
