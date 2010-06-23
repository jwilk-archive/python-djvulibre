tex_files = $(wildcard *.tex)
pdf_files = $(tex_files:.tex=.pdf)
djvu_files = $(pdf_files:.pdf=.djvu)

.PHONY: all
all: $(djvu_files)

%.pdf: %.tex
	pdflatex $(<)
	pdflatex $(<)

%.djvu: %.pdf
	pdf2djvu $(<) -o $(@)

.PHONY: clean
clean:
	rm -f $(pdf_files) $(djvu_files) *.log *.out *.aux

# vim:ts=4 sw=4 noet
