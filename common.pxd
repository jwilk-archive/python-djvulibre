# Copyright (c) 2008 Jakub Wilk <ubanus@users.sf.net>

# C library

ctypedef int size_t

cdef extern from 'stdio.h':
	ctypedef struct FILE

cdef extern from 'stdlib.h':
	void libc_free 'free'(void* ptr)

cdef extern from 'string.h':
	int strcmp(char *s1, char *s2)

# Python library

cdef extern from 'Python.h':

	void* py_malloc 'PyMem_Malloc'(size_t)
	void py_free 'PyMem_Free'(void*)

	int typecheck 'PyObject_TypeCheck'(object o, object type)
	int is_short_int 'PyInt_Check'(object)
	int is_long_int 'PyLong_Check'(object)
	int is_unicode 'PyUnicode_Check'(object)
	int is_string 'PyString_Check'(object)
	int is_slice 'PySlice_Check'(object)
	int is_file 'PyFile_Check'(object)

	object encode_utf8 'PyUnicode_AsUTF8String'(object)
	int string_to_charp_and_size 'PyString_AsStringAndSize'(object, char**, Py_ssize_t*) except -1
	char* string_to_charp 'PyString_AsString'(object) except NULL
	object charp_to_string 'PyString_FromStringAndSize'(char *, Py_ssize_t)

	FILE* file_to_cfile 'PyFile_AsFile'(object)

cdef int is_int(object o):
	return is_short_int(o) or is_long_int(o)

# vim:ts=4 sw=4 noet
