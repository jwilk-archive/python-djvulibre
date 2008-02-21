cdef extern from "libdjvu/miniexp.h":
	struct cexp_s "miniexp_s"
	ctypedef cexp_s* cexp_t "miniexp_t"

cdef object public_c2py(cexp_t)
cdef cexp_t public_py2c(object)

# vim:ts=4 sw=4 noet
