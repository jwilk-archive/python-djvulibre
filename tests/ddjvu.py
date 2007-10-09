from djvu.ddjvu import *

class ContextTest:
	'''
	>>> x = Context()
	>>> x.cache_size
	10485760L
	>>> x.cache_size = -100
	Traceback (most recent call last):
	...
	ValueError: 0 < cache_size < 2 * (sys.maxint + 1) is not satisfied
	>>> x.cache_size = 0
	Traceback (most recent call last):
	...
	ValueError: 0 < cache_size < 2 * (sys.maxint + 1) is not satisfied
	>>> x.cache_size = 100
	>>> x.cache_size
	100L
	>>> x.cache_size = (1 << 32) - 1
	>>> x.cache_size == (1 << 32) - 1
	True
	>>> x.cache_size = 1 << 32
	Traceback (most recent call last):
	...
	ValueError: 0 < cache_size < 2 * (sys.maxint + 1) is not satisfied
	>>> x.cache_size == (1 << 32) - 1
	True
	>>> x.clear_cache()

	>>> x.get_message(wait = False) is None
	True

	>>> del x
	'''

class DocumentTest:
	'''
	>>> Document()
	Traceback (most recent call last):
	...
	InstantiationError
	'''

class PageTest:
	'''
	>>> Page()
	Traceback (most recent call last):
	...
	InstantiationError
	'''

class JobTest:
	'''
	>>> Job()
	Traceback (most recent call last):
	...
	InstantiationError
	'''

class MessageTest:
	'''
	>>> Message()
	Traceback (most recent call last):
	...
	InstantiationError
	'''

class StreamTest:
	'''
	>>> Stream(None, 42)
	Traceback (most recent call last):
	...
	TypeError: Argument 'document' has incorrect type (expected ddjvu.Document, got NoneType)
	'''

if __name__ == '__main__':
	import doctest
	doctest.testmod()

# vim:ts=4 sw=4 noet
