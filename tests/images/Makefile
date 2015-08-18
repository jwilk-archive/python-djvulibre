# Copyright © 2010-2015 Jakub Wilk <jwilk@jwilk.net>
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

PDF2DJVU = pdf2djvu

tex_files = $(wildcard *.tex)
pdf_files = $(tex_files:.tex=.pdf)
djvu_files = $(pdf_files:.pdf=.djvu)

.PHONY: all
all: $(djvu_files)

%.pdf: %.tex
	pdflatex $(<)
	pdflatex $(<)

%.djvu: %.pdf
	$(PDF2DJVU) $(<) -o $(@)

.PHONY: clean
clean:
	rm -f $(pdf_files) *.log *.out *.aux

# vim:ts=4 sts=4 sw=4 noet
