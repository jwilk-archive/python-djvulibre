cdef extern from "libdjvu/miniexp.h":

	struct miniexp_s
	ctypedef miniexp_s* miniexp_t
	
	int miniexp_is_int "miniexp_numberp"(miniexp_t sexp)
	int miniexp_to_int(miniexp_t sexp)
	miniexp_t int_to_miniexp "miniexp_number"(int n)
	
	int miniexp_is_symbol "miniexp_symbolp"(miniexp_t sexp)
	char* miniexp_to_symbol "miniexp_to_name"(miniexp_t sexp)
	miniexp_t symbol_to_miniexp "miniexp_symbol"(char* name)

def MiniExp(value):
	if isinstance(value, (int, long)):
		return MiniExpInt(value)
	elif isinstance(value, str):
		return MiniExpSymbol(value)
	else:
		raise TypeError

cdef class _MiniExp:
	cdef miniexp_t _value
	
	def __repr__(self):
		return 'MiniExp(%r)' % self.get_value()

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


# vim:ts=4 sw=4 noet
