# Copyright (c) 2007 Jakub Wilk <ubanus@users.sf.net>

cdef extern from 'libdjvu/miniexp.h':
	int cexp_is_int 'miniexp_numberp'(cexp_t sexp)
	int cexp_to_int 'miniexp_to_int'(cexp_t sexp)
	cexp_t int_to_cexp 'miniexp_number'(int n)
	
	int cexp_is_symbol 'miniexp_symbolp'(cexp_t sexp)
	char* cexp_to_symbol 'miniexp_to_name'(cexp_t sexp)
	cexp_t symbol_to_cexp 'miniexp_symbol'(char* name)

	cexp_t cexp_nil 'miniexp_nil'
	cexp_t cexp_dummy 'miniexp_dummy'
	int cexp_is_list 'miniexp_listp'(cexp_t exp)
	int cexp_is_nonempty_list 'miniexp_consp'(cexp_t exp)
	int cexp_length 'miniexp_length'(cexp_t exp)
	cexp_t cexp_head 'miniexp_car'(cexp_t exp)
	cexp_t cexp_tail 'miniexp_cdr'(cexp_t exp)
	cexp_t cexp_nth 'miniexp_nth'(int n, cexp_t exp)
	cexp_t pair_to_cexp 'miniexp_cons'(cexp_t head, cexp_t tail)
	cexp_t cexp_replace_head 'miniexp_rplaca'(cexp_t exp, cexp_t new_head)
	cexp_t cexp_replace_tail 'miniexp_rplacd'(cexp_t exp, cexp_t new_tail)
	cexp_t cexp_reverse_list 'miniexp_reverse'(cexp_t exp)

	int cexp_is_str 'miniexp_stringp'(cexp_t cexp)
	char* cexp_to_str 'miniexp_to_str'(cexp_t cexp)
	cexp_t str_to_cexp 'miniexp_string'(char* s)
	cexp_t cexp_substr 'miniexp_substring'(char* s, int n)
	cexp_t cexp_concat 'miniexp_concat'(cexp_t cexp_list)

	cexp_t lock_gc 'minilisp_acquire_gc_lock'(cexp_t cexp)
	cexp_t unlock_gc 'minilisp_release_gc_lock'(cexp_t cexp)
	
	cdef extern struct cvar_s 'minivar_s'
	ctypedef cvar_s cvar_t 'minivar_t'

	cvar_t* cvar_new 'minivar_alloc'()
	void cvar_free 'minivar_free'(cvar_t* v)
	cexp_t* cvar_ptr 'minivar_pointer'(cvar_t* v)

	int (*io_puts 'minilisp_puts')(char *s)
	int (*io_getc 'minilisp_getc')()
	int (*io_ungetc 'minilisp_ungetc')(int c)
	cexp_t cexp_read 'miniexp_read'()
	cexp_t cexp_print 'miniexp_prin'(cexp_t cexp)
	cexp_t cexp_printw 'miniexp_pprin'(cexp_t cexp, int width)

cdef extern from 'stdio.h':
	int EOF

cdef object myio_stdin
cdef object myio_stdout
cdef int myio_buffer
myio_buffer = -1

cdef void myio_reset():
	import sys
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

cdef class _WrappedCExp:
	cdef cvar_t* cvar

	def __new__(self):
		self.cvar = cvar_new()

	cdef cexp_t cexp(self):
		return cvar_ptr(self.cvar)[0]

	def print_into(self, stdout, width = None):
		cdef cexp_t cexp
		global myio_stdout
		cexp = self.cexp()
		myio_stdout = stdout
		if width is None:
			cexp_print(cexp)
		else:
			cexp_printw(cexp, width)
		myio_reset()

	def as_string(self, width = None):
		from cStringIO import StringIO
		stdout = StringIO()
		try:
			self.print_into(stdout)
			return stdout.getvalue()
		finally:
			stdout.close()

	def __dealloc__(self):
		cvar_free(self.cvar)

cdef _WrappedCExp wexp(cexp_t cexp):
	cdef _WrappedCExp wexp
	wexp = _WrappedCExp()
	cvar_ptr(wexp.cvar)[0] = cexp
	return wexp

class Symbol(str):

	def __repr__(self):
		return 'Symbol(%s)' % str.__repr__(self)
	
	def __eq__(self, other):
		if not isinstance(other, Symbol):
			return False
		else:
			return str.__eq__(self, other)
	
	def __neq__(self, other):
		return not self.__eq__(other)

class Expression(object):
	pass

def Expression__new__(cls, value):
	if isinstance(value, (int, long)):
		return IntExpression(value)
	elif isinstance(value, Symbol):
		return SymbolExpression(value)
	elif isinstance(value, str):
		return StringExpression(value)
	else:
		try:
			iter(value)
		except TypeError:
			raise
		else:
			return ListExpression(value)

def Expression_from_stream(stdin):
	global myio_stdin
	try:
		myio_stdin = stdin
		try:
			return _c2py(cexp_read())
		except _InvalidExpression:
			raise ExpressionSyntaxError
	finally:
		myio_reset()

def Expression_from_string(str):
	from cStringIO import StringIO
	stdin = StringIO(str)
	try:
		return Expression.from_stream(stdin)
	finally:
		stdin.close()

Expression.__new__ = staticmethod(Expression__new__)
Expression.from_string = staticmethod(Expression_from_string)
Expression.from_stream = staticmethod(Expression_from_stream)
del Expression__new__, Expression_from_string, Expression_from_stream

cdef object _Expression_richcmp(object left, object right, int op):
	if not isinstance(left, _Expression):
		return NotImplemented
	elif not isinstance(right, _Expression):
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

cdef class _Expression:
	cdef _WrappedCExp wexp

	def print_into(self, stdout, width = None):
		return self.wexp.print_into(stdout, width)

	def as_string(self, width = None):
		return self.wexp.as_string(width)
	
	def __str__(self):
		return self.as_string()

	property value:
		def __get__(self):
			return self.get_value()

	def __richcmp__(self, other, int op):
		return _Expression_richcmp(self, other, op)

	def __repr__(self):
		return 'Expression(%r)' % (self.value,)

cdef class IntExpression(_Expression):

	def __new__(self, value):
		if isinstance(value, _WrappedCExp):
			self.wexp = value
		elif isinstance(value, (int, long)):
			if -1 << 29 <= value < 1 << 29:
				self.wexp = wexp(int_to_cexp(value))
			else:
				raise ValueError
		else:
			raise TypeError

	def __nonzero__(self):
		return bool(self.value)

	def __int__(self):
		return self.value

	def __long__(self):
		return 0L + self.value

	def get_value(self):
		return cexp_to_int(self.wexp.cexp())

	def __richcmp__(self, other, int op):
		return _Expression_richcmp(self, other, op)

	def __hash__(self):
		return hash(self.value)

cdef class SymbolExpression(_Expression):

	def __new__(self, value):
		if isinstance(value, _WrappedCExp):
			self.wexp = value
		elif isinstance(value, str):
			self.wexp = wexp(symbol_to_cexp(value))
		else:
			raise TypeError

	def get_value(self):
		return Symbol(cexp_to_symbol(self.wexp.cexp()))

	def __richcmp__(self, other, int op):
		return _Expression_richcmp(self, other, op)

	def __hash__(self):
		return hash(self.value)

cdef class StringExpression(_Expression):

	def __new__(self, value):
		if isinstance(value, _WrappedCExp):
			self.wexp = value
		elif isinstance(value, str):
			self.wexp = wexp(str_to_cexp(value))
		else:
			raise TypeError

	def get_value(self):
		return cexp_to_str(self.wexp.cexp())

	def __richcmp__(self, other, int op):
		return _Expression_richcmp(self, other, op)

	def __hash__(self):
		return hash(self.value)

class _InvalidExpression(ValueError):
	pass

class ExpressionSyntaxError(SyntaxError):
	pass

cdef _Expression _c2py(cexp_t cexp):
	if cexp == cexp_dummy:
		raise _InvalidExpression
	_wexp = wexp(cexp)
	if cexp_is_int(cexp):
		result = IntExpression(_wexp)
	elif cexp_is_symbol(cexp):
		result = SymbolExpression(_wexp)
	elif cexp_is_list(cexp):
		result = ListExpression(_wexp)
	elif cexp_is_str(cexp):
		result = StringExpression(_wexp)
	else:
		raise ValueError
	return result

cdef _WrappedCExp _build_list_cexp(object items):
	cdef cexp_t cexp
	lock_gc(NULL)
	try:
		cexp = cexp_nil
		Expression_ = Expression
		for item in items:
			cexp = pair_to_cexp((<_Expression>Expression_(item)).wexp.cexp(), cexp)
		cexp = cexp_reverse_list(cexp)
		return wexp(cexp)
	finally:
		unlock_gc(NULL)

cdef class ListExpression(_Expression):

	def __new__(self, items):
		if isinstance(items, _WrappedCExp):
			self.wexp = items
		else:
			self.wexp = _build_list_cexp(items)

	def __nonzero__(self):
		return self.wexp.cexp() != cexp_nil

	def __len__(self):
		cdef cexp_t cexp
		cdef int n
		cexp = self.wexp.cexp()
		n = 0
		while cexp != cexp_nil:
			cexp = cexp_tail(cexp)
			n = n + 1
		return n

	def __getitem__(self, key):
		cdef cexp_t cexp
		cdef int n
		cexp = self.wexp.cexp()
		if isinstance(key, (int, long)):
			n = key
			if n < 0:
				n = n + len(self)
			if n < 0:
				raise IndexError('list index of out range')
			while True:
				if cexp == cexp_nil:
					raise IndexError('list index of out range')
				if n > 0:
					n = n - 1
					cexp = cexp_tail(cexp)
				else:
					cexp = cexp_head(cexp)
					break
		elif isinstance(key, slice):
			if (isinstance(key.start, int)) or key.start is None and key.stop is None and key.step is None:
				n = key.start or 0
				if n < 0:
					n = n + len(self)
				while n > 0 and cexp != cexp_nil:
					cexp = cexp_tail(cexp)
					n = n - 1
			else:
				raise NotImplementedError('only [n:] slices are supported')
		else:
			raise TypeError
		return _c2py(cexp)

	def __setitem__(self, key, value):
		cdef cexp_t cexp
		cdef cexp_t prev_cexp
		cdef cexp_t new_cexp
		cdef int n
		cexp = self.wexp.cexp()
		new_cexp = (<_Expression>Expression(value)).wexp.cexp()
		if isinstance(key, (int, long)):
			n = key
			if n < 0:
				n = n + len(self)
			if n < 0:
				raise IndexError('list index of out range')
			while True:
				if cexp == cexp_nil:
					raise IndexError('list index of out range')
				if n > 0:
					n = n - 1
					cexp = cexp_tail(cexp)
				else:
					cexp_replace_head(cexp, new_cexp)
					break
		elif isinstance(key, slice):
			if not cexp_is_list(new_cexp):
				raise TypeError
			if (isinstance(key.start, int)) or key.start is None and key.stop is None and key.step is None:
				n = key.start or 0
				if n < 0:
					n = n + len(self)
				prev_cexp = cexp_nil
				while n > 0 and cexp != cexp_nil:
					prev_cexp = cexp
					cexp = cexp_tail(cexp)
					n = n - 1
				if prev_cexp == cexp_nil:
					self.wexp = wexp(new_cexp)
				else:
					cexp_replace_tail(prev_cexp, new_cexp)
			else:
				raise NotImplementedError('only [n:] slices are supported')
		else:
			raise TypeError

	def __iter__(self):
		return _ListExpressionIterator(self)

	def get_value(self):
		cdef cexp_t current
		current = self.wexp.cexp()
		result = []
		append = result.append
		while current != cexp_nil:
			append(_c2py(cexp_head(current)).get_value())
			current = cexp_tail(current)
		return tuple(result)

cdef class _ListExpressionIterator:

	cdef ListExpression expression
	cdef cexp_t cexp

	def __new__(self, ListExpression expression not None):
		self.expression = expression
		self.cexp = expression.wexp.cexp()
	
	def __next__(self):
		cdef cexp_t cexp
		cexp = self.cexp
		if cexp == cexp_nil:
			raise StopIteration
		self.cexp = cexp_tail(cexp)
		cexp = cexp_head(cexp)
		return _c2py(cexp)

# vim:ts=4 sw=4 noet
