cdef extern from "libdjvu/miniexp.h":

	extern struct miniexp_s
	
	extern int miniexp_numberp(miniexp_s* sexp)
	extern int miniexp_to_int(miniexp_s* sexp)
	extern miniexp_s* miniexp_number(int n)
	
	int miniexp_symbolp(miniexp_s* sexp)
	char* miniexp_to_name(miniexp_s* sexp)
	miniexp_s* miniexp_symbol(char* name)

cdef class MiniExp:
	cdef miniexp_s* _value

	def __new__(self, value):
		if isinstance(value, int):
			self._value = miniexp_number(value)
		elif isinstance(value, str):
			self._value = miniexp_symbol(value)
		else:
			raise TypeError

	def __repr__(self):
		cdef miniexp_s *value
		value = self._value
		if miniexp_numberp(value):
			return 'MiniExp(%d)' % miniexp_to_int(value)
		elif miniexp_symbolp(value):
			return 'MiniExp(%r)' % miniexp_to_name(value)
		else:
			raise TypeError

	def __dealloc__(self):
		pass		

# vim:ts=4 sw=4 noet
