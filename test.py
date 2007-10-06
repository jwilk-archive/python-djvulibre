from miniexp import *

class MiniExpNumberTest:
	'''
	>>> MiniExp(3)
	MiniExp(3)
	
	>>> MiniExp(42L)
	MiniExp(42)
	
	>>> MiniExp(1 << 30)
	Traceback (most recent call last):
	...
	ValueError
	
	>>> MiniExp('foobar')
	MiniExp('foobar')

	>>> MiniExp([[1,2], 3, [4,5], ['quux']])
	MiniExp(((1, 2), 3, (4, 5), ('quux',)))
	
	'''

if __name__ == '__main__':
	import doctest
	doctest.testmod()

# vim:ts=4 sw=4 noet
