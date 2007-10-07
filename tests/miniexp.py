from miniexp import *

class ExpressionNumberTest:
	'''
	>>> x = Expression(3)
	>>> x
	Expression(3)
	>>> str(x)
	'3'
	
	>>> Expression(42L)
	Expression(42)
	
	>>> Expression(1 << 30)
	Traceback (most recent call last):
	...
	ValueError
	
	>>> x = Expression(Symbol('foobar'))
	>>> x
	Expression(Symbol('foobar'))
	>>> str(x)
	'foobar'

	>>> x = Expression('foobar')
	>>> x
	Expression('foobar')
	>>> str(x)
	'"foobar"'

	>>> x = Expression([[1, 2], 3, [4, 5, Symbol('baz')], ['quux']])
	>>> x
	Expression(((1, 2), 3, (4, 5, Symbol('baz')), ('quux',)))
	>>> str(x)
	'((1 2) 3 (4 5 baz) ("quux"))'
	>>> repr(x) == repr(Expression.from_string(str(x)))
	True
	
	'''

if __name__ == '__main__':
	import doctest
	doctest.testmod()

# vim:ts=4 sw=4 noet
