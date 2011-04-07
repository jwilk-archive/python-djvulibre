# encoding=UTF-8
# Copyright © 2007, 2008, 2010, 2011 Jakub Wilk <jwilk@jwilk.net>
#
# This package is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This package is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

from __future__ import with_statement

import collections
import copy
import tempfile

import pickle
try:
    import cPickle as cpickle
except ImportError:
    cpickle = None

from djvu.sexpr import *

from common import *

def assert_pickle_equal(obj):
    for pickle_module in pickle, cpickle:
        if pickle_module is None:
            continue
        for protocol in 0, 1, 2:
            pickled_obj = pickle_module.dumps(obj, protocol=protocol)
            repickled_obj = pickle_module.loads(pickled_obj)
            assert_equal(obj, repickled_obj)

class test_int_expressions():

    def test_short(self):
        x = Expression(3)
        assert_repr(x, 'Expression(3)')
        assert_true(x is Expression(x))
        assert_equal(x.value, 3)
        assert_equal(str(x), '3')
        assert_repr(x, repr(Expression.from_string(str(x))))
        assert_equal(int(x), 3)
        if not py3k:
            long_x = long(x)
            assert_equal(type(long_x), long)
            assert_equal(long_x, L(3))
        assert_equal(x, Expression(3))
        assert_not_equal(x, Expression(-3))
        assert_equal(hash(x), x.value)
        assert_not_equal(x, 3)

    def test_long(self):
        x = Expression(L(42))
        assert_repr(x, 'Expression(42)')

    def test_limits(self):
        assert_equal(Expression((1 << 29) - 1).value, (1 << 29) - 1)
        assert_equal(Expression(-1 << 29).value, -1 << 29)
        with raises(ValueError, 'value not in range(-2 ** 29, 2 ** 29)'):
            Expression(1 << 29)
        with raises(ValueError, 'value not in range(-2 ** 29, 2 ** 29)'):
            Expression((-1 << 29) - 1)

    def test_bool(self):
        assert_equal(Expression(1) and 42, 42)
        assert_equal(Expression(0) or 42, 42)

    def test_pickle(self):
        x = Expression(42)
        assert_pickle_equal(x)

def test_symbols():

    for name in 'eggs', u('ветчина'):
        symbol = Symbol(name)
        assert_equal(type(symbol), Symbol)
        assert_equal(symbol, Symbol(name))
        assert_true(symbol is Symbol(name))
        if py3k:
            assert_equal(str(symbol), name)
        else:
            assert_equal(str(symbol), name.encode('UTF-8'))
            assert_equal(unicode(symbol), name)
        assert_not_equal(symbol, name)
        assert_not_equal(symbol, name.encode('UTF-8'))
        assert_equal(hash(symbol), hash(name.encode('UTF-8')))
        assert_pickle_equal(symbol)

def test_expressions():
    x = Expression(Symbol('eggs'))
    assert_repr(x, "Expression(Symbol('eggs'))")
    assert_true(x is Expression(x))
    assert_equal(x.value, Symbol('eggs'))
    assert_equal(str(x), 'eggs')
    assert_repr(x, repr(Expression.from_string(str(x))))
    assert_equal(x, Expression(Symbol('eggs')))
    assert_not_equal(x, Expression('eggs'))
    assert_not_equal(x, Symbol('eggs'))
    assert_equal(hash(x), hash('eggs'))
    assert_pickle_equal(x)

def test_string_expressions():
    x = Expression('eggs')
    assert_repr(x, "Expression('eggs')")
    assert_true(x is Expression(x))
    assert_equal(x.value, 'eggs')
    assert_equal(str(x), '"eggs"')
    assert_repr(x, repr(Expression.from_string(str(x))))
    assert_equal(x, Expression('eggs'))
    assert_not_equal(x, Expression(Symbol('eggs')))
    assert_not_equal(x, 'eggs')
    assert_equal(hash(x), hash('eggs'))
    assert_pickle_equal(x)

class test_unicode_expressions():

    def test1(self):
        x = Expression(u('eggs'))
        assert_repr(x, "Expression('eggs')")
        assert_true(x is Expression(x))

    def test2(self):
        x = Expression(u('żółw'))
        if py3k:
            assert_repr(x, "Expression('żółw')")
        else:
            assert_repr(x, r"Expression('\xc5\xbc\xc3\xb3\xc5\x82w')")

class test_list_expressions():

    def test1(self):
        x = Expression(())
        assert_repr(x, "Expression(())")
        y = Expression(x)
        assert_true(x is y)
        assert_equal(x.value, ())
        assert_equal(len(x), 0)
        assert_equal(bool(x), False)
        assert_equal(list(x), [])

    def test2(self):
        x = Expression([[1, 2], 3, [4, 5, Symbol('baz')], ['quux']])
        assert_repr(x, "Expression(((1, 2), 3, (4, 5, Symbol('baz')), ('quux',)))")
        y = Expression(x)
        assert_repr(y, repr(x))
        assert_false(x is y)
        assert_equal(x.value, ((1, 2), 3, (4, 5, Symbol('baz')), ('quux',)))
        assert_equal(str(x), '((1 2) 3 (4 5 baz) ("quux"))')
        assert_repr(x, repr(Expression.from_string(str(x))))
        assert_equal(len(x), 4)
        assert_equal(bool(x), True)
        assert_equal(tuple(x), (Expression((1, 2)), Expression(3), Expression((4, 5, Symbol('baz'))), Expression(('quux',))))
        with raises(TypeError, 'key must be an integer or a slice'):
            x[object()]
        assert_equal(x[1], Expression(3))
        assert_equal(x[-1][0], Expression('quux'))
        with raises(IndexError, 'list index of out range'):
            x[6]
        with raises(IndexError, 'list index of out range'):
            x[-6]
        assert_equal(x[:].value, x.value)
        assert_repr(x[1:], "Expression((3, (4, 5, Symbol('baz')), ('quux',)))")
        assert_repr(x[-2:], "Expression(((4, 5, Symbol('baz')), ('quux',)))")
        x[-2:] = 4, 5, 6
        assert_repr(x, 'Expression(((1, 2), 3, 4, 5, 6))')
        x[0] = 2
        assert_repr(x, 'Expression((2, 3, 4, 5, 6))')
        x[:] = (1, 3, 5)
        assert_repr(x, 'Expression((1, 3, 5))')
        x[3:] = 7,
        assert_repr(x, 'Expression((1, 3, 5, 7))')
        with raises(NotImplementedError, 'only [n:] slices are supported'):
            x[object():]
        with raises(NotImplementedError, 'only [n:] slices are supported'):
            x[:2]
        with raises(NotImplementedError, 'only [n:] slices are supported'):
            x[object():] = []
        with raises(NotImplementedError, 'only [n:] slices are supported'):
            x[:2] = []
        with raises(TypeError, 'can only assign a list expression'):
            x[:] = 0
        assert_equal(x, Expression((1, 3, 5, 7)))
        assert_not_equal(x, Expression((2, 4, 6)))
        assert_not_equal(x, (1, 3, 5, 7))
        with raises(TypeError, "unhashable type: 'ListExpression'"):
            hash(x)

    def test_insert(self):
        lst = []
        expr = Expression(())
        for pos in [-8, 4, 6, -5, -7, 5, 7, 2, -3, 8, 10, -2, 1, -9, -10, -4, -6, 0, 9, 3, -1]:
            lst.insert(pos, pos)
            assert_true(expr.insert(pos, pos) is None)
            assert_equal(expr, Expression(lst))
            assert_equal(list(expr.value), lst)

    def test_append(self):
        expr = Expression(())
        for i in range(10):
            assert_true(expr.append(i) is None)
            assert_equal(expr, Expression(range(i + 1)))
            assert_equal(list(expr.value), list(range(i + 1)))

    def test_extend(self):
        lst = []
        expr = Expression(())
        for ext in [1], [], [2, 3]:
            lst.extend(ext)
            expr.extend(ext)
            assert_equal(expr, Expression(lst))
            assert_equal(list(expr.value), lst)
        with raises(TypeError, "'int' object is not iterable"):
            expr.extend(0)

    def test_inplace_add(self):
        lst = []
        expr0 = expr = Expression(())
        for ext in [], [1], [], [2, 3]:
            lst += ext
            expr += ext
            assert_equal(expr, Expression(lst))
            assert_equal(list(expr.value), lst)
        assert_true(expr is expr0)
        with raises(TypeError, "'int' object is not iterable"):
            expr += 0

    def test_pop(self):
        expr = Expression([0, 1, 2, 3, 4, 5, 6])
        assert_equal(expr.pop(0), Expression(0))
        assert_equal(expr, Expression([1, 2, 3, 4, 5, 6]))
        with raises(IndexError, 'pop index of out range'):
            expr.pop(6)
        assert_equal(expr.pop(5), Expression(6))
        assert_equal(expr, Expression([1, 2, 3, 4, 5]))
        assert_equal(expr.pop(-1), Expression(5))
        assert_equal(expr, Expression([1, 2, 3, 4]))
        assert_equal(expr.pop(-2), Expression(3))
        assert_equal(expr, Expression([1, 2, 4]))
        assert_equal(expr.pop(1), Expression(2))
        assert_equal(expr, Expression([1, 4]))
        expr.pop()
        expr.pop()
        with raises(IndexError, 'pop from empty list'):
            expr.pop()
        for i in range(-2, 3):
            with raises(IndexError, 'pop from empty list'):
                expr.pop(i)

    def test_delitem(self):
        expr = Expression([0, 1, 2, 3, 4, 5, 6])
        del expr[0]
        assert_equal(expr, Expression([1, 2, 3, 4, 5, 6]))
        with raises(IndexError, 'pop index of out range'):
            expr.pop(6)
        del expr[5]
        assert_equal(expr, Expression([1, 2, 3, 4, 5]))
        del expr[-1]
        assert_equal(expr, Expression([1, 2, 3, 4]))
        del expr[-2]
        assert_equal(expr, Expression([1, 2, 4]))
        del expr[1]
        assert_equal(expr, Expression([1, 4]))
        del expr[1:]
        assert_equal(expr, Expression([1]))
        del expr[:]
        assert_equal(expr, Expression([]))
        for i in range(-2, 3):
            with raises(IndexError, 'pop from empty list'):
                del expr[i]

    def test_remove(self):
        expr = Expression([0, 1, 2, 3, 4, 5, 6])
        expr.remove(Expression(0))
        assert_equal(expr, Expression([1, 2, 3, 4, 5, 6]))
        with raises(IndexError, 'item not in list'):
            expr.remove(Expression(0))
        expr.remove(Expression(6))
        assert_equal(expr, Expression([1, 2, 3, 4, 5]))
        expr.remove(Expression(5))
        assert_equal(expr, Expression([1, 2, 3, 4]))
        expr.remove(Expression(3))
        assert_equal(expr, Expression([1, 2, 4]))
        expr.remove(Expression(2))
        assert_equal(expr, Expression([1, 4]))
        expr.remove(Expression(4))
        expr.remove(Expression(1))
        with raises(IndexError, 'item not in list'):
            expr.remove(Expression(-1))

    def test_contains(self):
        expr = Expression(())
        assert_false(Expression(42) in expr)
        lst = (1, 2, 3)
        expr = Expression(lst)
        for x in lst:
            assert_false(x in expr)
            assert_true(Expression(x) in expr)
        assert_false(Expression(max(lst) + 1) in expr)

    def test_index(self):
        expr = Expression(())
        with raises(ValueError, 'value not in list'):
            expr.index(Expression(42))
        lst = [1, 2, 3]
        expr = Expression(lst)
        for x in lst:
            i = lst.index(x)
            j = expr.index(Expression(x))
            assert_equal(i, j)
        with raises(ValueError, 'value not in list'):
            expr.index(Expression(max(lst) + 1))

    def test_count(self):
        lst = [1, 2, 2, 3, 2]
        expr = Expression(lst)
        for x in lst + [max(lst) + 1]:
            i = lst.count(x)
            j = expr.count(Expression(x))
            assert_equal(i, j)

    def test_reverse(self):
        for lst in (), (1, 2, 3):
            expr = Expression(lst)
            assert_equal(
                Expression(reversed(expr)),
                Expression(reversed(lst))
            )
            assert_equal(
                Expression(reversed(expr)).value,
                tuple(reversed(lst))
            )
            assert_true(expr.reverse() is None)
            assert_equal(
                expr,
                Expression(reversed(lst))
            )
            assert_equal(
                expr.value,
                tuple(reversed(lst))
            )

    def test_copy1(self):
        x = Expression([1, [2], 3])
        y = Expression(x)
        x[1][0] = 0
        assert_repr(x, 'Expression((1, (0,), 3))')
        assert_repr(y, 'Expression((1, (0,), 3))')
        x[1] = 0
        assert_repr(x, 'Expression((1, 0, 3))')
        assert_repr(y, 'Expression((1, (0,), 3))')

    def test_copy2(self):
        x = Expression([1, [2], 3])
        y = copy.copy(x)
        x[1][0] = 0
        assert_repr(x, 'Expression((1, (0,), 3))')
        assert_repr(y, 'Expression((1, (0,), 3))')
        x[1] = 0
        assert_repr(x, 'Expression((1, 0, 3))')
        assert_repr(y, 'Expression((1, (0,), 3))')

    def test_copy3(self):
        x = Expression([1, [2], 3])
        y = copy.deepcopy(x)
        x[1][0] = 0
        assert_repr(x, 'Expression((1, (0,), 3))')
        assert_repr(y, 'Expression((1, (2,), 3))')
        x[1] = 0
        assert_repr(x, 'Expression((1, 0, 3))')
        assert_repr(y, 'Expression((1, (2,), 3))')

    if sys.version_info >= (2, 6):
        def test_abc(self):
            x = Expression(())
            assert_true(isinstance(x, collections.MutableSequence))
            assert_true(isinstance(iter(x), collections.Iterator))

    def test_pickle(self):
        for lst in (), (1, 2, 3), (1, (2, 3)):
            x = Expression(lst)
            assert_pickle_equal(x)

def test_expression_parser():

    def test_badstring():
        with raises(ExpressionSyntaxError):
            Expression.from_string('(1')

    def test_bad_io():
        assert getattr(Expression.from_file, None) is None
        with raises(ExpressionSyntaxError):
            Expression.from_stream(42)

    def test_stringio():
        fp = StringIO('(eggs) (ham)')
        def read():
            Expression.from_stream(fp)
        x = read()
        assert_repr(x, "Expression((Symbol('eggs'),))")
        x = read()
        assert_repr(x, "Expression((Symbol('ham'),))")
        with raises(ExpressionSyntaxError):
            x = read()

    def test_fileio():
        fp = tempfile.TemporaryFile()
        def read():
            Expression.from_stream(fp)
        if not py3k:
            assert_equal(type(fp), file)
        fp.write('(eggs) (ham)')
        fp.seek(0)
        x = read()
        assert_repr(x, "Expression((Symbol('eggs'),))")
        x = read()
        assert_repr(x, "Expression((Symbol('ham'),))")
        with raises(ExpressionSyntaxError):
            x = read()

class test_expression_writer():

    expr = Expression([Symbol('eggs'), Symbol('ham')])

    def test_bad_io(self):
        self.expr.print_into(42)

    def test_stringio(self):
        fp = StringIO()
        self.expr.print_into(fp)
        assert_equal(fp.getvalue(), '(eggs ham)')

    def test_fileio_text(self):
        fp = tempfile.TemporaryFile(mode='w+t')
        if not py3k and os.name == 'posix':
            assert_equal(type(fp), file)
        self.expr.print_into(fp)
        fp.seek(0)
        assert_equal(fp.read(), '(eggs ham)')

    def test_fileio_binary(self):
        fp = tempfile.TemporaryFile(mode='w+b')
        if not py3k and os.name == 'posix':
            assert_equal(type(fp), file)
        self.expr.print_into(fp)
        fp.seek(0)
        assert_equal(fp.read(), b('(eggs ham)'))

# vim:ts=4 sw=4 et
