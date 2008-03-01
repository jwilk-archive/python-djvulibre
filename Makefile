.PHONY: all
all:
	python setup.py build_ext --inplace --debug

.PHONY: test
test: test-sexpr test-decode

test-%: tests/%.py all
	python $(<)

.PHONY: clean
clean:
	$(RM) djvu/*.so *.c python-build-stamp-*
	$(RM) -R build/

# vim:ts=4 sw=4 noet
