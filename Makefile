PYVERSION = 2.4
PYHOME = /usr
PYARCH = $(PYHOME)/$(ARCH)
PYINCLUDE = -I$(PYHOME)/include/python$(PYVERSION)
PYLIB = \
	-L$(PYHOME)/lib/python$(PYVERSION)/config \
	-lpython$(PYVERSION) -ldl -lpthread -lutil -lm

PYX_FILES = $(wildcard *.pyx)
O_FILES = $(PYX_FILES:.pyx=.o)

%.c: %.pyx
	pyrexc $(<)

%.o: %.c
	$(CC) -c -fPIC $(PYINCLUDE) $(<)

.PHONY: all
all: $(O_FILES)
	python setup.py build_ext --inplace

.PHONY: test
test: all
	python test.py

.PHONY: clea
clean:
	$(RM) -f *.c *.o *.so

# vim:ts=4 sw=4 noet
