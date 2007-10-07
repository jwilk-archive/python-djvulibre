# Copyright (c) 2007 Jakub Wilk <ubanus@users.sf.net>

cdef extern from "libdjvu/miniexp.h":
	cdef extern struct cexp_s "miniexp_s"
	ctypedef cexp_s* cexp_t "miniexp_t"

	int cexp_is_int "miniexp_numberp"(cexp_t sexp)
	int cexp_to_int "miniexp_to_int"(cexp_t sexp)
	cexp_t int_to_cexp "miniexp_number"(int n)
	
	int cexp_is_symbol "miniexp_symbolp"(cexp_t sexp)
	char* cexp_to_symbol "miniexp_to_name"(cexp_t sexp)
	cexp_t symbol_to_cexp "miniexp_symbol"(char* name)

	cexp_t cexp_nil "miniexp_nil"
	cexp_t cexp_dummy "miniexp_dummy"
	int cexp_is_list "miniexp_listp"(cexp_t exp)
	int cexp_is_nonempty_list "miniexp_consp"(cexp_t exp)
	int cexp_length "miniexp_length"(cexp_t exp)
	cexp_t cexp_head "miniexp_car"(cexp_t exp)
	cexp_t cexp_tail "miniexp_cdr"(cexp_t exp)
	cexp_t cexp_nth "miniexp_nth"(int n, cexp_t exp)
	cexp_t pair_to_cexp "miniexp_cons"(cexp_t head, cexp_t tail)
	cexp_t cexp_replace_head "miniexp_rplaca"(cexp_t exp, cexp_t new_head)
	cexp_t cexp_replace_tail "miniexp_rplacd"(cexp_t exp, cexp_t new_tail)
	cexp_t cexp_reverse_list "miniexp_reverse"(cexp_t exp)

	int cexp_is_str "miniexp_stringp"(cexp_t cexp)
	char* cexp_to_str "miniexp_to_str"(cexp_t cexp)
	cexp_t str_to_cexp "miniexp_string"(char* s)
	cexp_t cexp_substr "miniexp_substring"(char* s, int n)
	cexp_t cexp_concat "miniexp_concat"(cexp_t cexp_list)

	cexp_t lock_gc "minilisp_acquire_gc_lock"(cexp_t cexp)
	cexp_t unlock_gc "minilisp_release_gc_lock"(cexp_t cexp)
	
	cdef extern struct cvar_s "minivar_s"
	ctypedef cvar_s cvar_t "minivar_t"

	cvar_t* cvar_new "minivar_alloc"()
	void cvar_free "minivar_free"(cvar_t* v)
	cexp_t* cvar_ptr "minivar_pointer"(cvar_t* v)

	int (*io_puts "minilisp_puts")(char *s)
	int (*io_getc "minilisp_getc")()
	int (*io_ungetc "minilisp_ungetc")(int c)
	cexp_t cexp_read "miniexp_read"()
	cexp_t cexp_print "miniexp_prin"(cexp_t cexp)
	cexp_t cexp_printw "miniexp_pprin"(cexp_t cexp, int width)

cdef object myio_stdin
cdef object myio_stdout

cdef void myio_reset():
	import sys
	global myio_stdin, myio_stdout
	myio_stdin = sys.stdin
	myio_stdout = sys.stdout

cdef int myio_puts(char *s):
	myio_stdout.write(s)

cdef int myio_getc():
	return ord(myio_stdin.read(1))

cdef int myio_ungetc(int c):
	raise NotImplementedError

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

cdef void wexp_set(_WrappedCExp wexp, cexp_t cexp):
	cvar_ptr(wexp.cvar)[0] = cexp

cdef _WrappedCExp wexp(cexp_t cexp):
	wexp = _WrappedCExp()
	wexp_set(wexp, cexp)
	return wexp

class Symbol(str):

	def __repr__(self):
		return 'Symbol(%s)' % str.__repr__(self)

def Expression(value):
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

cdef class _Expression:
	cdef _WrappedCExp wexp

	def print_into(self, stdout, width = None):
		return self.wexp.print_into(stdout, width)

	def as_string(self, width = None):
		return self.wexp.as_string(width)
	
	def __str__(self):
		return self.as_string()

	def __repr__(self):
		return 'Expression(%r)' % (self.get_value(),)

cdef class IntExpression(_Expression):

	def __new__(self, value):
		if isinstance(value, _WrappedCExp):
			self.wexp = value
		elif isinstance(value, (int, long)):
			if -1 << 29 <= value <= 1 << 29:
				self.wexp = wexp(int_to_cexp(value))
			else:
				raise ValueError
		else:
			raise TypeError

	def get_value(self):
		return cexp_to_int(self.wexp.cexp())

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

cdef cexp_t _py2c(_Expression pyexp):
	return pyexp.wexp.cexp()

cdef _Expression _c2py(cexp_t cexp):
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
		raise TypeError
	return result

cdef class ListExpression(_Expression):

	cdef cexp_t _cexp

	def __new__(self, items):
		if isinstance(items, _WrappedCExp):
			self.wexp = items
			return
		lock_gc(NULL)
		self._cexp = cexp_nil
		for item in items:
			self._cexp = pair_to_cexp(_py2c(Expression(item)), self._cexp)
		self._cexp = cexp_reverse_list(self._cexp)
		self.wexp = wexp(self._cexp)
		unlock_gc(NULL)

	def get_value(self):
		cdef cexp_t current
		current = self.wexp.cexp()
		result = []
		while current != cexp_nil:
			result.append(_c2py(cexp_head(current)).get_value())
			current = cexp_tail(current)
		return tuple(result)

# vim:ts=4 sw=4 noet
