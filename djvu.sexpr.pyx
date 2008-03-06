# Copyright (c) 2007, 2008 Jakub Wilk <ubanus@users.sf.net>

'''
DjVuLibre bindings: module for handling Lisp S-expressions
'''

include 'common.pxi'

cdef extern from 'libdjvu/miniexp.h':
	int cexpr_is_int 'miniexp_numberp'(cexpr_t sexp)
	int cexpr_to_int 'miniexp_to_int'(cexpr_t sexp)
	cexpr_t int_to_cexpr 'miniexp_number'(int n)
	
	int cexpr_is_symbol 'miniexp_symbolp'(cexpr_t sexp)
	char* cexpr_to_symbol 'miniexp_to_name'(cexpr_t sexp)
	cexpr_t symbol_to_cexpr 'miniexp_symbol'(char* name)

	cexpr_t cexpr_nil 'miniexp_nil'
	cexpr_t cexpr_dummy 'miniexp_dummy'
	int cexpr_is_list 'miniexp_listp'(cexpr_t exp)
	int cexpr_is_nonempty_list 'miniexp_consp'(cexpr_t exp)
	int cexpr_length 'miniexp_length'(cexpr_t exp)
	cexpr_t cexpr_head 'miniexp_car'(cexpr_t exp)
	cexpr_t cexpr_tail 'miniexp_cdr'(cexpr_t exp)
	cexpr_t cexpr_nth 'miniexp_nth'(int n, cexpr_t exp)
	cexpr_t pair_to_cexpr 'miniexp_cons'(cexpr_t head, cexpr_t tail)
	cexpr_t cexpr_replace_head 'miniexp_rplaca'(cexpr_t exp, cexpr_t new_head)
	cexpr_t cexpr_replace_tail 'miniexp_rplacd'(cexpr_t exp, cexpr_t new_tail)
	cexpr_t cexpr_reverse_list 'miniexp_reverse'(cexpr_t exp)

	int cexpr_is_str 'miniexp_stringp'(cexpr_t cexpr)
	char* cexpr_to_str 'miniexp_to_str'(cexpr_t cexpr)
	cexpr_t str_to_cexpr 'miniexp_string'(char* s)
	cexpr_t cexpr_substr 'miniexp_substring'(char* s, int n)
	cexpr_t cexpr_concat 'miniexp_concat'(cexpr_t cexpr_list)

	cexpr_t lock_gc 'minilisp_acquire_gc_lock'(cexpr_t cexpr)
	cexpr_t unlock_gc 'minilisp_release_gc_lock'(cexpr_t cexpr)
	
	cvar_t* cvar_new 'minivar_alloc'()
	void cvar_free 'minivar_free'(cvar_t* v)
	cexpr_t* cvar_ptr 'minivar_pointer'(cvar_t* v)

	int (*io_puts 'minilisp_puts')(char *s)
	int (*io_getc 'minilisp_getc')()
	int (*io_ungetc 'minilisp_ungetc')(int c)
	cexpr_t cexpr_read 'miniexp_read'()
	cexpr_t cexpr_print 'miniexp_prin'(cexpr_t cexpr)
	cexpr_t cexpr_printw 'miniexp_pprin'(cexpr_t cexpr, int width)

cdef extern from 'stdio.h':
	int EOF

cdef object sys
import sys

cdef object StringIO
from cStringIO import StringIO

cdef object myio_stdin
cdef object myio_stdout
cdef int myio_buffer
myio_buffer = -1

cdef void myio_reset():
	global myio_stdin, myio_stdout
	myio_stdin = sys.stdin
	myio_stdout = sys.stdout
	myio_buffer = -1

cdef int myio_puts(char *s):
	myio_stdout.write(s)

cdef int myio_getc():
	global myio_buffer
	cdef int result
	result = myio_buffer
	if result >= 0:
		myio_buffer = -1
	else:
		s = myio_stdin.read(1)
		if s:
			result = ord(s)
		else:
			result = EOF
	return result

cdef int myio_ungetc(int c):
	global myio_buffer
	if myio_buffer >= 0:
		raise RuntimeError
	myio_buffer = c

io_puts = myio_puts
io_getc = myio_getc
io_ungetc = myio_ungetc

cdef object the_sentinel
the_sentinel = object()

cdef class _WrappedCExpr:

	def __cinit__(self, object sentinel):
		if sentinel is not the_sentinel:
			raise_instantiation_error(type(self))
		self.cvar = cvar_new()

	cdef cexpr_t cexpr(self):
		return cvar_ptr(self.cvar)[0]

	cdef object print_into(self, object stdout, object width):
		cdef cexpr_t cexpr
		global myio_stdout
		if width is None:
			pass
		elif not is_int(width):
			raise TypeError
		elif width <= 0:
			raise ValueError
		cexpr = self.cexpr()
		myio_stdout = stdout
		if width is None:
			cexpr_print(cexpr)
		else:
			cexpr_printw(cexpr, width)
		myio_reset()

	cdef object as_string(self, object width):
		stdout = StringIO()
		try:
			self.print_into(stdout, width)
			return stdout.getvalue()
		finally:
			stdout.close()

	def __dealloc__(self):
		cvar_free(self.cvar)

cdef _WrappedCExpr wexpr(cexpr_t cexpr):
	cdef _WrappedCExpr wexpr
	wexpr = _WrappedCExpr(sentinel = the_sentinel)
	cvar_ptr(wexpr.cvar)[0] = cexpr
	return wexpr

cdef class _MissingCExpr(_WrappedCExpr):

	cdef object print_into(self, object stdout, object width):
		raise NotImplementedError
	
	cdef object as_string(self, object width):
		raise NotImplementedError

cdef _MissingCExpr wexpr_missing():
	return _MissingCExpr(the_sentinel)

class Symbol(str):

	def __repr__(self):
		return '%s(%s)' % (get_type_name(SymbolType), str.__repr__(self))
	
	def __eq__(self, other):
		if not typecheck(other, Symbol):
			return False
		else:
			return str.__eq__(self, other)
	
	def __neq__(self, other):
		return not self.__eq__(other)

def Expression__new__(cls, value):
	'''
	Expression(value) -> an expression.
	'''
	if is_int(value):
		return IntExpression(value)
	elif typecheck(value, Symbol):
		return SymbolExpression(value)
	elif is_unicode(value):
		return StringExpression(encode_utf8(value))
	elif is_string(value):
		return StringExpression(str(value))
	else:
		try:
			it = iter(value)
		except TypeError:
			raise
		else:
			return ListExpression(it)

def Expression_from_stream(stdin):
	'''
	Expression.from_stream(stream) -> an expression.

	Read an expression from a stream.
	'''
	global myio_stdin
	try:
		myio_stdin = stdin
		try:
			return _c2py(cexpr_read())
		except _InvalidExpression:
			raise ExpressionSyntaxError
	finally:
		myio_reset()

def Expression_from_string(str):
	'''
	Expression.from_string(s) -> an expression.

	Read an expression from a string.
	'''
	stdin = StringIO(str)
	try:
		return Expression.from_stream(stdin)
	finally:
		stdin.close()

class Expression(BaseExpression):

	'''
	Notes about the textual represenation of S-expressions
	------------------------------------------------------

	Special characters are:

	* the parenthesis ``(`` and ``)``,
	* the double quote ``"``,
	* the vertical bar ``|``.
	
	Symbols are represented by their name. Vertical bars ``|`` can be used to
	delimit names that contain blanks, special characters, non printable
	characters, non ascii characters, or can be confused as a number.
	
	Numbers follow the syntax specified by the C function ``strtol()`` with
	``base=0``.
	
	Strings are delimited by double quotes. All C string escapes are
	recognized. Non-printable ascii characters must be escaped.
	
	List are represented by an open parenthesis ``(`` followed by the space
	separated list elements, followed by a closing parenthesis ``)``.
	
	When the ``cdr`` of the last pair is non zero, the closed parenthesis is
	preceded by a space, a dot ``.``, a space, and the textual representation
	of the ``cdr``. (This is only partially supported by Python bindings.)

	'''
	__new__ = staticmethod(Expression__new__)
	from_string = staticmethod(Expression_from_string)
	from_stream = staticmethod(Expression_from_stream)

del Expression__new__, Expression_from_string, Expression_from_stream

cdef object BaseExpression_richcmp(object left, object right, int op):
	if not typecheck(left, BaseExpression):
		return NotImplemented
	elif not typecheck(right, BaseExpression):
		return NotImplemented
	elif op == 0:
		result = left.value <  right.value
	elif op == 1:
		result = left.value <= right.value
	elif op == 2:
		result = left.value == right.value
	elif op == 3:
		result = left.value != right.value
	elif op == 4:
		result = left.value >  right.value
	elif op == 5:
		result = left.value >= right.value
	else:
		raise SystemError
	return bool(result)

cdef class BaseExpression:
	'''
	Don't use this class directly. Use the `Expression` class instead.
	'''

	cdef _WrappedCExpr wexpr

	def __cinit__(self, *args, **kwargs):
		self.wexpr = wexpr_missing()

	def print_into(self, stdout, width = None):
		'''
		expr.print_into(file[, width]).
		
		Print the expression into the file.
		'''
		self.wexpr.print_into(stdout, width)

	def as_string(self, width = None):
		'''
		expr.as_string([width]).

		Return a string representation of the expression.
		'''
		return self.wexpr.as_string(width)
	
	def __str__(self):
		return self.as_string()

	property value:
		'''
		The actual "pythonic" value of the expression.
		'''	
		def __get__(self):
			return self._get_value()
	
	def _get_value(self):
		raise NotImplementedError

	def __richcmp__(self, other, int op):
		return BaseExpression_richcmp(self, other, op)

	def __repr__(self):
		return '%s(%r)' % (get_type_name(ExpressionType), self.value)

def IntExpression__new__(cls, value):
	'''
	IntExpression(n) -> an integer expression.
	'''
	cdef BaseExpression self
	self = BaseExpression.__new__(cls)
	if typecheck(value, _WrappedCExpr):
		self.wexpr = value
	elif is_int(value):
		if -1 << 29 <= value < 1 << 29:
			self.wexpr = wexpr(int_to_cexpr(value))
		else:
			raise ValueError
	else:
		raise TypeError
	return self

class IntExpression(Expression):

	'''
	IntExpression can represent any integer in range(-2 ** 29, 2 ** 29).
	'''

	__new__ = staticmethod(IntExpression__new__)
	
	def __nonzero__(self):
		return bool(self.value)

	def __int__(self):
		return self.value

	def __long__(self):
		return 0L + self.value

	def _get_value(BaseExpression self not None):
		return cexpr_to_int(self.wexpr.cexpr())

	def __richcmp__(self, other, int op):
		return BaseExpression_richcmp(self, other, op)

	def __hash__(self):
		return hash(self.value)

del IntExpression__new__

def SymbolExpression__new__(cls, value):
	'''
	SymbolExpression(Symbol(s)) -> a symbol expression.
	'''
	cdef BaseExpression self
	self = BaseExpression.__new__(cls)
	if typecheck(value, _WrappedCExpr):
		self.wexpr = value
	elif typecheck(value, str):
		self.wexpr = wexpr(symbol_to_cexpr(value))
	else:
		raise TypeError
	return self

class SymbolExpression(Expression):

	__new__ = staticmethod(SymbolExpression__new__)

	def _get_value(BaseExpression self not None):
		return Symbol(cexpr_to_symbol(self.wexpr.cexpr()))

	def __richcmp__(self, other, int op):
		return BaseExpression_richcmp(self, other, op)

	def __hash__(self):
		return hash(self.value)

del SymbolExpression__new__

def StringExpression__new__(cls, value):
	'''
	SymbolExpression(s) -> a string expression.
	'''
	cdef BaseExpression self
	self = BaseExpression.__new__(cls)
	if typecheck(value, _WrappedCExpr):
		self.wexpr = value
	elif is_string(value):
		self.wexpr = wexpr(str_to_cexpr(value))
	else:
		raise TypeError
	return self

class StringExpression(Expression):

	__new__ = staticmethod(StringExpression__new__)

	def _get_value(BaseExpression self not None):
		return cexpr_to_str(self.wexpr.cexpr())

	def __richcmp__(self, other, int op):
		return BaseExpression_richcmp(self, other, op)

	def __hash__(self):
		return hash(self.value)

del StringExpression__new__

class _InvalidExpression(ValueError):
	pass

class ExpressionSyntaxError(Exception):
	'''
	Invalid expression syntax.
	'''
	pass

cdef _WrappedCExpr public_py2c(object o):
	cdef BaseExpression pyexpr
	pyexpr = Expression(o)
	if pyexpr is None:
		raise TypeError
	return pyexpr.wexpr

cdef object public_c2py(cexpr_t cexpr):
	return _c2py(cexpr)

cdef BaseExpression _c2py(cexpr_t cexpr):
	if cexpr == cexpr_dummy:
		raise _InvalidExpression
	_wexpr = wexpr(cexpr)
	if cexpr_is_int(cexpr):
		result = IntExpression(_wexpr)
	elif cexpr_is_symbol(cexpr):
		result = SymbolExpression(_wexpr)
	elif cexpr_is_list(cexpr):
		result = ListExpression(_wexpr)
	elif cexpr_is_str(cexpr):
		result = StringExpression(_wexpr)
	else:
		raise ValueError
	return result

cdef _WrappedCExpr _build_list_cexpr(object items):
	cdef cexpr_t cexpr
	cdef BaseExpression citem
	lock_gc(NULL)
	try:
		cexpr = cexpr_nil
		for item in items:
			citem = Expression(item)
			if citem is None:
				raise TypeError
			cexpr = pair_to_cexpr(citem.wexpr.cexpr(), cexpr)
		cexpr = cexpr_reverse_list(cexpr)
		return wexpr(cexpr)
	finally:
		unlock_gc(NULL)

def ListExpression__new__(cls, items):
	'''
	ListExpression(iterable) -> a list expression.
	'''
	cdef BaseExpression self
	self = BaseExpression.__new__(cls)
	if typecheck(items, _WrappedCExpr):
		self.wexpr = items
	else:
		self.wexpr = _build_list_cexpr(items)
	return self

class ListExpression(Expression):

	__new__ = staticmethod(ListExpression__new__)

	def __nonzero__(BaseExpression self not None):
		return self.wexpr.cexpr() != cexpr_nil

	def __len__(BaseExpression self not None):
		cdef cexpr_t cexpr
		cdef int n
		cexpr = self.wexpr.cexpr()
		n = 0
		while cexpr != cexpr_nil:
			cexpr = cexpr_tail(cexpr)
			n = n + 1
		return n

	def __getitem__(BaseExpression self not None, key):
		cdef cexpr_t cexpr
		cdef int n
		cexpr = self.wexpr.cexpr()
		if is_int(key):
			n = key
			if n < 0:
				n = n + len(self)
			if n < 0:
				raise IndexError('list index of out range')
			while True:
				if cexpr == cexpr_nil:
					raise IndexError('list index of out range')
				if n > 0:
					n = n - 1
					cexpr = cexpr_tail(cexpr)
				else:
					cexpr = cexpr_head(cexpr)
					break
		elif is_slice(key):
			if is_int(key.start) or key.start is None and key.stop is None and key.step is None:
				n = key.start or 0
				if n < 0:
					n = n + len(self)
				while n > 0 and cexpr != cexpr_nil:
					cexpr = cexpr_tail(cexpr)
					n = n - 1
			else:
				raise NotImplementedError('only [n:] slices are supported')
		else:
			raise TypeError
		return _c2py(cexpr)

	def __setitem__(BaseExpression self not None, key, value):
		cdef cexpr_t cexpr
		cdef cexpr_t prev_cexpr
		cdef cexpr_t new_cexpr
		cdef int n
		cdef BaseExpression pyexpr
		cexpr = self.wexpr.cexpr()
		pyexpr = Expression(value)
		if pyexpr is None:
			raise TypeError
		new_cexpr = pyexpr.wexpr.cexpr()
		if is_int(key):
			n = key
			if n < 0:
				n = n + len(self)
			if n < 0:
				raise IndexError('list index of out range')
			while True:
				if cexpr == cexpr_nil:
					raise IndexError('list index of out range')
				if n > 0:
					n = n - 1
					cexpr = cexpr_tail(cexpr)
				else:
					cexpr_replace_head(cexpr, new_cexpr)
					break
		elif is_slice(key):
			if not cexpr_is_list(new_cexpr):
				raise TypeError
			if is_slice(key) or key.start is None and key.stop is None and key.step is None:
				n = key.start or 0
				if n < 0:
					n = n + len(self)
				prev_cexpr = cexpr_nil
				while n > 0 and cexpr != cexpr_nil:
					prev_cexpr = cexpr
					cexpr = cexpr_tail(cexpr)
					n = n - 1
				if prev_cexpr == cexpr_nil:
					self.wexpr = wexpr(new_cexpr)
				else:
					cexpr_replace_tail(prev_cexpr, new_cexpr)
			else:
				raise NotImplementedError('only [n:] slices are supported')
		else:
			raise TypeError

	def __iter__(self):
		return _ListExpressionIterator(self)
	
	def __hash__(self):
		raise TypeError('unhashable type: \'%s\'' % (get_type_name(type(self)),))

	def _get_value(BaseExpression self not None):
		cdef cexpr_t current
		current = self.wexpr.cexpr()
		result = []
		append = result.append
		while current != cexpr_nil:
			append(_c2py(cexpr_head(current))._get_value())
			current = cexpr_tail(current)
		return tuple(result)

del ListExpression__new__

cdef class _ListExpressionIterator:

	cdef BaseExpression expression
	cdef cexpr_t cexpr

	def __cinit__(self, BaseExpression expression not None):
		self.expression = expression
		self.cexpr = expression.wexpr.cexpr()
	
	def __next__(self):
		cdef cexpr_t cexpr
		cexpr = self.cexpr
		if cexpr == cexpr_nil:
			raise StopIteration
		self.cexpr = cexpr_tail(cexpr)
		cexpr = cexpr_head(cexpr)
		return _c2py(cexpr)

cdef object SymbolType
cdef object ExpressionType

SymbolType = Symbol
ExpressionType = Expression

__all__ = ('Symbol', 'Expression', 'IntExpression', 'SymbolExpression', 'StringExpression', 'ListExpression', 'ExpressionSyntaxError')
__author__ = 'Jakub Wilk <ubanus@users.sf.net>'
__version__ = PYTHON_DJVULIBRE_VERSION

# vim:ts=4 sw=4 noet ft=pyrex
