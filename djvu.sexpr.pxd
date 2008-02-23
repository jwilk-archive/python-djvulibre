cdef extern from "libdjvu/miniexp.h":
	struct cexpr_s 'miniexp_s'
	ctypedef cexpr_s* cexpr_t 'miniexp_t'

	cdef extern struct cvar_s 'minivar_s'
	ctypedef cvar_s cvar_t 'minivar_t'

cdef class _WrappedCExpr:
	cdef cvar_t* cvar
	cdef cexpr_t cexpr(self)
	cdef object print_into(self, object, object)
	cdef object as_string(self, object)

cdef object public_c2py(cexpr_t)
cdef _WrappedCExpr public_py2c(object)

# vim:ts=4 sw=4 noet
