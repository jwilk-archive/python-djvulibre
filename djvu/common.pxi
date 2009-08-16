# Copyright © 2008, 2009 Jakub Wilk <ubanus@users.sf.net>
#
# This package is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This package is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

# python-distutils preprocessor macros

cdef extern from *:
    char* PYTHON_DJVULIBRE_VERSION

# C library

ctypedef int size_t

cdef extern from 'stdio.h':
    ctypedef struct FILE

cdef extern from 'stdlib.h':
    void libc_free 'free'(void* ptr) nogil

cdef extern from 'string.h':
    int strcmp(char *s1, char *s2) nogil
    size_t strlen(char *s) nogil

# Python library

cdef extern from 'Python.h':

    void* py_malloc 'PyMem_Malloc'(size_t)
    void py_free 'PyMem_Free'(void*)

    int is_short_int 'PyInt_Check'(object)
    int is_long_int 'PyLong_Check'(object)
    int is_float 'PyFloat_Check'(object)
    int is_unicode 'PyUnicode_Check'(object)
    int is_string 'PyString_Check'(object)
    int is_slice 'PySlice_Check'(object)
    int is_file 'PyFile_Check'(object)

    object encode_utf8 'PyUnicode_AsUTF8String'(object)
    object decode_utf8_ex 'PyUnicode_DecodeUTF8'(char *, Py_ssize_t, char *)
    int string_to_charp_and_size 'PyString_AsStringAndSize'(object, char**, Py_ssize_t*) except -1
    char* string_to_charp 'PyString_AsString'(object) except NULL
    object charp_to_string 'PyString_FromStringAndSize'(char *, Py_ssize_t)

    object int 'PyNumber_Int'(object)
    object bool 'PyBool_FromLong'(long)
    object voidp_to_int 'PyLong_FromVoidPtr'(void *)

    FILE* file_to_cfile 'PyFile_AsFile'(object)

    int list_append 'PyList_Append'(object, object) except -1

    cdef object richcmp 'PyObject_RichCompare'(object, object, int)

cdef extern from 'pythread.h':
    ctypedef void* Lock 'PyThread_type_lock'
    cdef Lock allocate_lock 'PyThread_allocate_lock'()
    cdef void free_lock 'PyThread_free_lock'(Lock lock)
    cdef int acquire_lock 'PyThread_acquire_lock'(Lock lock, int mode) nogil
    cdef void release_lock 'PyThread_release_lock'(Lock lock)
    
    ctypedef enum:
        WAIT_LOCK
        NOWAIT_LOCK

cdef extern from 'object.h':
    ctypedef struct PyTypeObject:
        char *tp_name
    ctypedef struct PyObject:
        PyTypeObject *ob_type
    int _typecheck 'PyObject_TypeCheck'(object o, PyTypeObject* type)

cdef int is_int(object o):
    return is_short_int(o) or is_long_int(o)

cdef object type(object o):
    return <object>((<PyObject*>o).ob_type)

cdef char* get_type_name(object type):
    return (<PyTypeObject*>type).tp_name

cdef int typecheck(object o, object type):
    return _typecheck(o, <PyTypeObject*> type)

cdef void raise_instantiation_error(object cls) except *:
    raise TypeError, 'cannot create \'%s\' instances' % get_type_name(cls)

cdef object decode_utf8(char* s):
    return decode_utf8_ex(s, strlen(s), NULL)

cdef object Exception, ValueError, TypeError, SystemError, StopIteration, MemoryError, OverflowError, SystemExit, KeyError, IndexError, IOError, NotImplementedError, KeyboardInterrupt, AttributeError
from exceptions import Exception, ValueError, TypeError, SystemError, StopIteration, MemoryError, OverflowError, SystemExit, KeyError, IndexError, IOError, NotImplementedError, KeyboardInterrupt, AttributeError

# vim:ts=4 sw=4 et ft=pyrex
