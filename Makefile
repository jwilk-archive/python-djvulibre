.PHONY: all
all:
	python setup.py build_ext --inplace

.PHONY: test
test: all
	python test.py

.PHONY: clean
clean:
	$(RM) -f *.c *.o *.so

# vim:ts=4 sw=4 noet
