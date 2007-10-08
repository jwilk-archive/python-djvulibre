from miniexp import *

class IntExpressionTest:
	'''
	>>> x = Expression(3)
	>>> x
	Expression(3)

	>>> x.value
	3

	>>> str(x)
	'3'

	>>> repr(x) == repr(Expression.from_string(str(x)))
	True
	
	>>> int(x)
	3
	>>> long(x)
	3L
	
	>>> Expression(42L)
	Expression(42)

	>>> [Expression(i).value == i for i in (1 << 29 - 1, -1 << 29)]
	[True, True]
	>>> Expression(1 << 29)
	Traceback (most recent call last):
	...
	ValueError
	>>> Expression((-1 << 29) - 1)
	Traceback (most recent call last):
	...
	ValueError
	'''

class SymbolExpressionTest:
	'''
	>>> x = Expression(Symbol('foobar'))
	>>> x
	Expression(Symbol('foobar'))

	>>> x.value
	Symbol('foobar')

	>>> str(x)
	'foobar'
	
	>>> repr(x) == repr(Expression.from_string(str(x)))
	True
	'''

class StringExpressionTest:
	'''
	>>> x = Expression('foobar')
	>>> x
	Expression('foobar')

	>>> x.value
	'foobar'

	>>> str(x)
	'"foobar"'
	
	>>> repr(x) == repr(Expression.from_string(str(x)))
	True
	'''

class ListExpressionTest:
	'''
	>>> x = Expression(())
	>>> x
	Expression(())

	>>> x.value
	()

	>>> len(x)
	0

	>>> bool(x)
	False

	>>> list(x)
	[]

	>>> x = Expression([[1, 2], 3, [4, 5, Symbol('baz')], ['quux']])
	>>> x
	Expression(((1, 2), 3, (4, 5, Symbol('baz')), ('quux',)))

	>>> x.value
	((1, 2), 3, (4, 5, Symbol('baz')), ('quux',))

	>>> str(x)
	'((1 2) 3 (4 5 baz) ("quux"))'
	
	>>> repr(x) == repr(Expression.from_string(str(x)))
	True

	>>> len(x)
	4

	>>> bool(x)
	True

	>>> tuple(x)
	(Expression((1, 2)), Expression(3), Expression((4, 5, Symbol('baz'))), Expression(('quux',)))
	
	>>> x[1]
	Expression(3)
	
	>>> x[-1][0]
	Expression('quux')
	
	>>> x[6]
	Traceback (most recent call last):
	...
	IndexError: list index of out range
	>>> x[-6]
	Traceback (most recent call last):
	...
	IndexError: list index of out range
	
	>>> x[:].value == x.value
	True
	
	>>> x[1:]
	Expression((3, (4, 5, Symbol('baz')), ('quux',)))
	>>> x[-2:]
	Expression(((4, 5, Symbol('baz')), ('quux',)))

	>>> x[-2:] = 4, 5, 6
	>>> x
	Expression(((1, 2), 3, 4, 5, 6))
	>>> x[0] = 2
	>>> x
	Expression((2, 3, 4, 5, 6))
	>>> x[:] = (1, 3, 5)
	>>> x
	Expression((1, 3, 5))
	>>> x[3:] = 7,
	>>> x
	Expression((1, 3, 5, 7))
	
	'''

class ExpressionParser:
	'''
	>>> Expression.from_string('(1')
	Traceback (most recent call last):
	...
	ExpressionSyntaxError
	'''

if __name__ == '__main__':
	import doctest
	doctest.testmod()

# vim:ts=4 sw=4 noet
