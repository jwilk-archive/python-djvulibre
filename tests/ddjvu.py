from djvu.ddjvu import *

class ContextTest:
	'''
	>>> x = Context()
	>>> x.cache_size
	10485760L
	>>> x.cache_size = -100
	Traceback (most recent call last):
	...
	ValueError: 0 < cache_size < 4294967296 is not satisfied
	>>> x.cache_size = 0
	Traceback (most recent call last):
	...
	ValueError: 0 < cache_size < 4294967296 is not satisfied
	>>> x.cache_size = 100
	>>> x.cache_size
	100L
	>>> x.cache_size = (1 << 32) - 1
	>>> x.cache_size == (1 << 32) - 1
	True
	>>> x.cache_size = 1 << 32
	Traceback (most recent call last):
	...
	ValueError: 0 < cache_size < 4294967296 is not satisfied
	>>> x.cache_size == (1 << 32) - 1
	True
	>>> del x.cache_size
	>>> x.cache_size
	10485760L
	>>> x.clear_cache()
	>>> del x
	'''

if __name__ == '__main__':
	import doctest
	doctest.testmod()


# vim:ts=4 sw=4 noet
