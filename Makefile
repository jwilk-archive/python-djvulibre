PYTHON = python

.PHONY: all
all:
	$(PYTHON) setup.py build_ext --inplace --debug

.PHONY: test
test: test-sexpr test-decode

test-%: tests/%.py all
	$(PYTHON) $(<)

.PHONY: clean
clean:
	$(RM) djvu/*.so djvu/*.c djvu/*.py[co] python-build-stamp-* *.py[co]
	$(RM) -R build/ *.egg-info/

# vim:ts=4 sw=4 noet
