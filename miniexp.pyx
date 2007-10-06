cdef extern from "libdjvu/miniexp.h":

	struct miniexp_s
	ctypedef miniexp_s* miniexp_t
	
	int miniexp_is_int "miniexp_numberp"(miniexp_t sexp)
	int miniexp_to_int(miniexp_t sexp)
	miniexp_t int_to_miniexp "miniexp_number"(int n)
	
	int miniexp_is_symbol "miniexp_symbolp"(miniexp_t sexp)
	char* miniexp_to_symbol "miniexp_to_name"(miniexp_t sexp)
	miniexp_t symbol_to_miniexp "miniexp_symbol"(char* name)

	miniexp_t miniexp_nil
	miniexp_t miniexp_dummy
	int miniexp_is_list "miniexp_listp"(miniexp_t exp)
	int miniexp_is_nonempty_list "miniexp_consp"(miniexp_t exp)
	int miniexp_length(miniexp_t exp)
	miniexp_t miniexp_head "miniexp_car"(miniexp_t exp)
	miniexp_t miniexp_tail "miniexp_cdr"(miniexp_t exp)
	miniexp_t miniexp_nth(int n, miniexp_t exp)
	miniexp_t pair_to_miniexp "miniexp_cons"(miniexp_t head, miniexp_t tail)
	miniexp_t miniexp_replace_head "miniexp_rplaca"(miniexp_t exp, miniexp_t new_head)
	miniexp_t miniexp_replace_tail "miniexp_rplacd"(miniexp_t exp, miniexp_t new_tail)
	miniexp_t miniexp_reverse_list "miniexp_reverse"(miniexp_t exp)

def MiniExp(value):
	if isinstance(value, (int, long)):
		return MiniExpInt(value)
	elif isinstance(value, str):
		return MiniExpSymbol(value)
	else:
		try:
			iter(value)
		except TypeError:
			raise
		else:
			return MiniExpList(value)

cdef class _MiniExp:
	cdef miniexp_t _value
	
	def __repr__(self):
		return 'MiniExp(%r)' % (self.get_value(),)

cdef class MiniExpInt(_MiniExp):

	def __new__(self, value):
		if not isinstance(value, (int, long)):
			raise TypeError
		if -1 << 29 <= value <= 1 << 29:
			self._value = int_to_miniexp(value)
		else:
			raise ValueError

	def get_value(self):
		return miniexp_to_int(self._value)

cdef class MiniExpSymbol(_MiniExp):

	def __new__(self, value):
		if isinstance(value, str):
			self._value = symbol_to_miniexp(value)
		else:
			raise TypeError

	def get_value(self):
		return miniexp_to_symbol(self._value)

cdef miniexp_t _py2c(_MiniExp pyexp):
	return pyexp._value

cdef void _py_set_value(_MiniExp pyexp, miniexp_t cexp):
	pyexp._value = cexp

cdef _MiniExp _c2py(miniexp_t cexp):
	if miniexp_is_int(cexp):
		result = MiniExpInt(0)
	elif miniexp_is_symbol(cexp):
		result = MiniExpSymbol('')
	elif miniexp_is_list(cexp):
		result = MiniExpList(())
	else:
		raise TypeError
	_py_set_value(result, cexp)
	return result

cdef class MiniExpList(_MiniExp):

	def __new__(self, items):
		self._value = miniexp_nil
		for item in items:
			self._value = pair_to_miniexp(_py2c(MiniExp(item)), self._value)
		self._value = miniexp_reverse_list(self._value)

	def get_value(self):
		cdef miniexp_t current
		current = self._value
		result = []
		while current != miniexp_nil:
			result.append(_c2py(miniexp_head(current)).get_value())
			current = miniexp_tail(current)
		return tuple(result)

# vim:ts=4 sw=4 noet
