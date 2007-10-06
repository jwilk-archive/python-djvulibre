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
	'''

if __name__ == '__main__':
	import doctest
	doctest.testmod()

# vim:ts=4 sw=4 noet
