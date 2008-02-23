cdef extern from "libdjvu/miniexp.h":
	struct cexp_s "miniexp_s"
	ctypedef cexp_s* cexp_t "miniexp_t"

	cdef extern struct cvar_s 'minivar_s'
	ctypedef cvar_s cvar_t 'minivar_t'

cdef class _WrappedCExp:
	cdef cvar_t* cvar
	cdef cexp_t cexp(self)
	cdef object print_into(self, object, object)
	cdef object as_string(self, object)

cdef object public_c2py(cexp_t)
cdef _WrappedCExp public_py2c(object)

# vim:ts=4 sw=4 noet
