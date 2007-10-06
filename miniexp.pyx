cdef extern from "libdjvu/miniexp.h":

	struct miniexp_s
	ctypedef miniexp_s* miniexp_t
	
	int miniexp_is_int "miniexp_numberp"(miniexp_t sexp)
	int miniexp_to_int(miniexp_t sexp)
	miniexp_t int_to_miniexp "miniexp_number"(int n)
	
	int miniexp_is_symbol "miniexp_symbolp"(miniexp_t sexp)
	char* miniexp_to_symbol "miniexp_to_name"(miniexp_t sexp)
	miniexp_t symbol_to_miniexp "miniexp_symbol"(char* name)

cdef class MiniExp:
	cdef miniexp_t _value

	def __new__(self, value):
		if isinstance(value, int):
			self._value = int_to_miniexp(value)
		elif isinstance(value, str):
			self._value = symbol_to_miniexp(value)
		else:
			raise TypeError

	def get_value(self):
		cdef miniexp_t value
		value = self._value
		if miniexp_is_int(value):
			return miniexp_to_int(value)
		elif miniexp_is_symbol(value):
			return miniexp_to_symbol(value)
		else:
			raise TypeError

	def __repr__(self):
		return 'MiniExp(%r)' % self.get_value()

	def __dealloc__(self):
		pass		

# vim:ts=4 sw=4 noet
