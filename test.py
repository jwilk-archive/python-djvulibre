from miniexp import *

class ExpressionNumberTest:
	'''
	>>> Expression(3)
	Expression(3)
	
	>>> Expression(42L)
	Expression(42)
	
	>>> Expression(1 << 30)
	Traceback (most recent call last):
	...
	ValueError
	
	>>> Expression(Symbol('foobar'))
	Expression(Symbol('foobar'))

	>>> Expression('foobar')
	Expression('foobar')

	>>> Expression([[1, 2], 3, [4, 5, Symbol('baz')], ['quux']])
	Expression(((1, 2), 3, (4, 5, Symbol('baz')), ('quux',)))
	
	'''

if __name__ == '__main__':
	import doctest
	doctest.testmod()

# vim:ts=4 sw=4 noet
