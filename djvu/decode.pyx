# Copyright © 2007, 2008, 2009, 2010, 2011 Jakub Wilk <jwilk@jwilk.net>
#
# This package is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This package is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

#cython: autotestdict=False

'''
DjVuLibre bindings: module for efficiently decoding and displaying DjVu documents.

Summary
-------
The DDJVU API provides for efficiently decoding and displaying DjVu documents.
It provides for displaying images without waiting for the complete DjVu data.
Images can be displayed as soon as sufficient data is available. A higher
quality image might later be displayed when further data is available. The DjVu
library achieves this using a complicated scheme involving multiple threads.
The DDJVU API hides this complexity with a familiar event model.
'''

include 'common.pxi'

cdef object weakref
import weakref

cdef object thread
IF PY3K:
    import _thread as thread
ELSE:
    import thread

cdef object Queue, Empty
IF PY3K:
    from queue import Queue, Empty
ELSE:
    from Queue import Queue, Empty

cdef object Condition
from threading import Condition

cdef object imap, izip
IF PY3K:
    imap = map
    izip = zip
ELSE:
    from itertools import imap, izip

cdef object sys, devnull, format_exc
import sys
from os import devnull
from traceback import format_exc

# The two lines below are solely to work-around Cython bug:
# http://bugs.debian.org/620859
cdef object MemoryError
IF PY3K:
    from builtins import MemoryError
ELSE:
    from exceptions import MemoryError

cdef object StringIO
IF PY3K:
    from io import StringIO
ELSE:
    from cStringIO import StringIO

cdef object Symbol, SymbolExpression, InvalidExpression
from djvu.sexpr import Symbol, SymbolExpression, InvalidExpression

cdef object the_sentinel
the_sentinel = object()

cdef object _context_loft, _document_loft, _document_weak_loft, _job_loft, _job_weak_loft
cdef Lock loft_lock
_context_loft = {}
_document_loft = set()
_document_weak_loft = weakref.WeakValueDictionary()
_job_loft = set()
_job_weak_loft = weakref.WeakValueDictionary()
loft_lock = allocate_lock()

cdef extern from 'libdjvu/ddjvuapi.h':
    ddjvu_context_t* ddjvu_context_create(char* program_name) nogil
    void ddjvu_context_release(ddjvu_context_t* context) nogil

    void ddjvu_cache_set_size(ddjvu_context_t* context, unsigned long cachesize) nogil
    unsigned long ddjvu_cache_get_size(ddjvu_context_t* context) nogil
    void ddjvu_cache_clear(ddjvu_context_t* context) nogil

    ddjvu_message_t* ddjvu_message_peek(ddjvu_context_t* context) nogil
    ddjvu_message_t* ddjvu_message_wait(ddjvu_context_t* context) nogil
    void ddjvu_message_pop(ddjvu_context_t* context) nogil

    void ddjvu_message_set_callback(ddjvu_context_t* context, ddjvu_message_callback_t callback, void* closure) nogil

    ddjvu_status_t ddjvu_job_status(ddjvu_job_t* job) nogil
    int ddjvu_job_done(ddjvu_job_t* job) nogil
    int ddjvu_job_error(ddjvu_job_t* job) nogil
    void ddjvu_job_stop(ddjvu_job_t* job) nogil
    void ddjvu_job_set_user_data(ddjvu_job_t* job, void* userdata) nogil
    void* ddjvu_job_get_user_data(ddjvu_job_t* job) nogil
    void ddjvu_job_release(ddjvu_job_t* job) nogil

    ddjvu_document_t* ddjvu_document_create(ddjvu_context_t* context, char* url, int cache) nogil
    ddjvu_document_t* ddjvu_document_create_by_filename(ddjvu_context_t* context, char* filename, int cache) nogil
    ddjvu_job_t* ddjvu_document_job(ddjvu_document_t* document) nogil
    void ddjvu_document_release(ddjvu_document_t* document) nogil

    void ddjvu_document_set_user_data(ddjvu_document_t* document, void* userdata) nogil
    void* ddjvu_document_get_user_data(ddjvu_document_t* document) nogil

    ddjvu_status_t ddjvu_document_decoding_status(ddjvu_document_t* document) nogil
    int ddjvu_document_decoding_done(ddjvu_document_t* document) nogil
    int ddjvu_document_decoding_error(ddjvu_document_t* document) nogil

    void ddjvu_stream_write(ddjvu_document_t* document, int streamid, char* data, unsigned long datalen) nogil
    void ddjvu_stream_close(ddjvu_document_t* document, int streamid, int stop) nogil

    ddjvu_document_type_t ddjvu_document_get_type(ddjvu_document_t* document) nogil
    int ddjvu_document_get_pagenum(ddjvu_document_t* document) nogil
    int ddjvu_document_get_filenum(ddjvu_document_t* document) nogil

    ddjvu_status_t ddjvu_document_get_fileinfo(ddjvu_document_t* document, int fileno, ddjvu_fileinfo_t* info) nogil
    int ddjvu_document_check_pagedata(ddjvu_document_t* document, int pageno) nogil

    ddjvu_status_t ddjvu_document_get_pageinfo(ddjvu_document_t* document, int pageno, ddjvu_pageinfo_t* info) nogil
    ddjvu_status_t ddjvu_document_get_pageinfo_imp(ddjvu_document_t* document, int pageno, ddjvu_pageinfo_t* info, unsigned int infosz) nogil
    char* ddjvu_document_get_pagedump(ddjvu_document_t* document, int pageno) nogil
    char* ddjvu_document_get_filedump(ddjvu_document_t* document, int fileno) nogil

    ddjvu_page_t* ddjvu_page_create_by_pageno(ddjvu_document_t* document, int pageno) nogil
    ddjvu_job_t* ddjvu_page_job(ddjvu_page_t* page) nogil

    void ddjvu_page_release(ddjvu_page_t* page) nogil
    void ddjvu_page_set_user_data(ddjvu_page_t* page, void* userdata) nogil
    void* ddjvu_page_get_user_data(ddjvu_page_t* page) nogil

    ddjvu_status_t ddjvu_page_decoding_status(ddjvu_page_t* page) nogil
    int ddjvu_page_decoding_done(ddjvu_page_t* page) nogil
    int ddjvu_page_decoding_error(ddjvu_page_t* page) nogil

    int ddjvu_page_get_width(ddjvu_page_t* page) nogil
    int ddjvu_page_get_height(ddjvu_page_t* page) nogil
    int ddjvu_page_get_resolution(ddjvu_page_t* page) nogil
    double ddjvu_page_get_gamma(ddjvu_page_t* page) nogil
    int ddjvu_page_get_version(ddjvu_page_t* page) nogil
    int ddjvu_code_get_version() nogil

    ddjvu_page_type_t ddjvu_page_get_type(ddjvu_page_t* page) nogil

    void ddjvu_page_set_rotation(ddjvu_page_t* page, ddjvu_page_rotation_t rot) nogil
    ddjvu_page_rotation_t ddjvu_page_get_rotation(ddjvu_page_t* page) nogil
    ddjvu_page_rotation_t ddjvu_page_get_initial_rotation(ddjvu_page_t* page) nogil

    int ddjvu_page_render(ddjvu_page_t* page, ddjvu_render_mode_t mode, ddjvu_rect_t* pagerect, ddjvu_rect_t* renderrect, ddjvu_format_t* pixelformat, unsigned long rowsize, char* imagebuffer) nogil

    ddjvu_rectmapper_t* ddjvu_rectmapper_create(ddjvu_rect_t* input, ddjvu_rect_t* output) nogil
    void ddjvu_rectmapper_modify(ddjvu_rectmapper_t* mapper, int rotation, int mirrorx, int mirrory) nogil
    void ddjvu_rectmapper_release(ddjvu_rectmapper_t* mapper) nogil
    void ddjvu_map_point(ddjvu_rectmapper_t* mapper, int* x, int* y) nogil
    void ddjvu_map_rect(ddjvu_rectmapper_t* mapper, ddjvu_rect_t* rect) nogil
    void ddjvu_unmap_point(ddjvu_rectmapper_t* mapper, int* x, int* y) nogil
    void ddjvu_unmap_rect(ddjvu_rectmapper_t* mapper, ddjvu_rect_t* rect) nogil

    ddjvu_format_t* ddjvu_format_create(ddjvu_format_style_t style, int nargs, unsigned int* args) nogil
    void ddjvu_format_set_row_order(ddjvu_format_t* format, int top_to_bottom) nogil
    void ddjvu_format_set_y_direction(ddjvu_format_t* format, int top_to_bottom) nogil
    void ddjvu_format_set_ditherbits(ddjvu_format_t* format, int bits) nogil
    void ddjvu_format_set_gamma(ddjvu_format_t* format, double gamma) nogil
    void ddjvu_format_release(ddjvu_format_t* format) nogil

    ddjvu_status_t ddjvu_thumbnail_status(ddjvu_document_t* document, int pagenum, int start) nogil

    int ddjvu_thumbnail_render(ddjvu_document_t* document, int pagenum, int* wptr, int* hptr, ddjvu_format_t* pixelformat, unsigned long rowsize, char* imagebuffer) nogil

    ddjvu_job_t* ddjvu_document_print(ddjvu_document_t* document, FILE* output, int optc, char** optv) nogil
    ddjvu_job_t* ddjvu_document_save(ddjvu_document_t* document, FILE* output, int optc, char** optv) nogil

    void ddjvu_miniexp_release(ddjvu_document_t* document, cexpr_t expr) nogil

    cexpr_t ddjvu_document_get_outline(ddjvu_document_t* document) nogil
    cexpr_t ddjvu_document_get_anno(ddjvu_document_t* document, int compat) nogil
    cexpr_t ddjvu_document_get_pagetext(ddjvu_document_t* document, int pageno, char* maxdetail) nogil
    cexpr_t ddjvu_document_get_pageanno(ddjvu_document_t* document, int pageno) nogil
    char* ddjvu_anno_get_bgcolor(cexpr_t annotations) nogil
    char* ddjvu_anno_get_zoom(cexpr_t annotations) nogil
    char* ddjvu_anno_get_mode(cexpr_t annotations) nogil
    char* ddjvu_anno_get_horizalign(cexpr_t annotations) nogil
    char* ddjvu_anno_get_vertalign(cexpr_t annotations) nogil
    cexpr_t* ddjvu_anno_get_hyperlinks(cexpr_t annotations) nogil
    cexpr_t* ddjvu_anno_get_metadata_keys(cexpr_t annotations) nogil
    char* ddjvu_anno_get_metadata(cexpr_t annotations, cexpr_t key) nogil

cdef extern from 'unistd.h':
    int dup(int)
    FILE *fdopen(int, char*)
    int fclose(FILE *)

IF HAVE_LANGINFO_H:
    cdef extern from 'langinfo.h':
        ctypedef enum nl_item:
            CODESET
        char *nl_langinfo(nl_item item)

DDJVU_VERSION = ddjvu_code_get_version()

FILE_TYPE_PAGE = 'P'
FILE_TYPE_THUMBNAILS = 'T'
FILE_TYPE_INCLUDE = 'I'

DOCUMENT_TYPE_UNKNOWN = DDJVU_DOCTYPE_UNKNOWN
DOCUMENT_TYPE_SINGLE_PAGE = DDJVU_DOCTYPE_SINGLEPAGE
DOCUMENT_TYPE_BUNDLED = DDJVU_DOCTYPE_BUNDLED
DOCUMENT_TYPE_INDIRECT = DDJVU_DOCTYPE_INDIRECT
DOCUMENT_TYPE_OLD_BUNDLED = DDJVU_DOCTYPE_OLD_BUNDLED
DOCUMENT_TYPE_OLD_INDEXED = DDJVU_DOCTYPE_OLD_INDEXED

cdef object check_sentinel(self, kwargs):
    if kwargs.get('sentinel') is not the_sentinel:
        raise_instantiation_error(type(self))

cdef object write_unraisable_exception(object cause):
    try:
        message = format_exc()
    except AttributeError:
        # This mostly happens during interpreter cleanup.
        # It's worthless to try to recover.
        raise SystemExit
    sys.stderr.write('Unhandled exception in thread started by %r\n%s\n' % (cause, message))

cdef class _FileWrapper:

    cdef object _file
    cdef FILE *cfile

    def __cinit__(self, object file, object mode):
        self._file = file
        self.cfile = NULL
        if not is_file(file):
            raise TypeError('file must be a real file object')
        IF PY3K:
            fd = file_to_fd(file)
            if fd == -1:
                posix_error(OSError)
            fd = dup(fd)
            if fd == -1:
                posix_error(OSError)
            self.cfile = fdopen(fd, mode)
            if self.cfile == NULL:
                posix_error(OSError)
        ELSE:
            self.cfile = file_to_cfile(file)

    cdef object close(self):
        IF PY3K:
            cdef int rc
            if self.cfile == NULL:
                return
            rc = fclose(self.cfile)
            self.cfile = NULL
            if rc != 0:
                posix_error(OSError)
        ELSE:
            if self._file is not None:
                self._file.flush()
                self._file = None
                self.cfile = NULL

    IF PY3K:
        def __dealloc__(self):
            cdef int rc
            if self.cfile == NULL:
                return
            rc = fclose(self.cfile)
            # XXX It's too late to handle errors.

class NotAvailable(Exception):
    '''
    A resource not (yet) available.
    '''

cdef object _NotAvailable_
_NotAvailable_ = NotAvailable

class DjVuLibreBug(Exception):

    '''
    A DjVuLibre bug was encountered.
    '''

    def __init__(self, debian_bug_no):
        Exception.__init__(
            self,
            'A DjVuLibre bug has been encountered.\n'
            'See <http://bugs.debian.org/%d> for details.\n'
            'Please upgrade your DjVuLibre.' % (debian_bug_no,)
        )

cdef class DocumentExtension:

    property document:

        '''
        Return the concerned Document.
        '''

        def __get__(self):
            return self._document

cdef class DocumentPages(DocumentExtension):

    '''
    Pages of a document.

    Use document.pages to obtain instances of this class.

    Page indexing is zero-based, i.e. pages[0] stands for the very first page.

    len(pages) might return 1 when called before receiving a DocInfoMessage.
    '''

    def __cinit__(self, Document document not None, **kwargs):
        check_sentinel(self, kwargs)
        self._document = document

    def __len__(self):
        return ddjvu_document_get_pagenum(self._document.ddjvu_document)

    def __getitem__(self, key):
        if is_int(key):
            if key < 0 or key >= len(self):
                raise IndexError('page number out of range')
            return Page(self.document, key)
        else:
            raise TypeError('page numbers must be integers')

cdef class Page:

    '''
    Page of a document.

    Use document.pages[N] to obtain instances of this class.
    '''

    def __cinit__(self, Document document not None, int n):
        self._document = document
        self._have_info = 0
        self._n = n

    property document:
        '''
        Return the Document which includes the page.
        '''
        def __get__(self):
            return self._document

    property file:
        '''
        Return a File associated with the page.
        '''
        def __get__(self):
            return self._document.files[self]

    property n:
        '''
        Return the page number.

        Page indexing is zero-based, i.e. 0 stands for the very first page.
        '''
        def __get__(self):
            return self._n

    property thumbnail:
        '''
        Return a Thumbnail for the page.
        '''
        def __get__(self):
            return Thumbnail(self)

    cdef object _get_info(self):
        cdef ddjvu_status_t status
        if self._have_info:
            return
        status = ddjvu_document_get_pageinfo(self._document.ddjvu_document, self._n, &self.ddjvu_pageinfo)
        ex = JobException_from_c(status)
        if ex is JobOK:
            return
        elif ex is JobStarted:
            raise _NotAvailable_
        else:
            raise ex

    def get_info(self, wait=1):
        '''
        P.get_info(wait=True) -> None

        Attempt to obtain information about the page without decoding the page.

        If wait is true, wait until the information is available.

        If the information is not available, raise NotAvailable exception.
        Then, start fetching the page data, which causes emission of
        PageInfoMessage messages with empty .page_job.

        Possible exceptions: NotAvailable, JobFailed.
        '''
        cdef ddjvu_status_t status
        if self._have_info:
            return
        if not wait:
            return self._get_info()
        while 1:
            self._document._condition.acquire()
            try:
                status = ddjvu_document_get_pageinfo(self._document.ddjvu_document, self._n, &self.ddjvu_pageinfo)
                ex = JobException_from_c(status)
                if ex is JobOK:
                    self._have_info = 1
                    return
                elif ex is JobStarted:
                    self._document._condition.wait()
                else:
                    raise ex
            finally:
                self._document._condition.release()

    property width:
        '''
        Return the page width, in pixels.

        Possible exceptions: NotAvailable, JobFailed.
        See Page.get_info() for details.
        '''
        def __get__(self):
            self._get_info()
            return self.ddjvu_pageinfo.width

    property height:
        '''
        Return the page height, in pixels.

        Possible exceptions: NotAvailable, JobFailed.
        See Page.get_info() for details.
        '''
        def __get__(self):
            self._get_info()
            return self.ddjvu_pageinfo.height

    property size:
        '''
        page.size == (page.width, page.height)

        Possible exceptions: NotAvailable, JobFailed.
        See Page.get_info() for details.
        '''
        def __get__(self):
            self._get_info()
            return self.ddjvu_pageinfo.width, self.ddjvu_pageinfo.height

    property dpi:
        '''
        Return the page resolution, in pixels per inch.

        Possible exceptions: NotAvailable, JobFailed.
        See Page.get_info() for details.
        '''
        def __get__(self):
            self._get_info()
            return self.ddjvu_pageinfo.dpi

    property rotation:
        '''
        Return the initial page rotation, in degrees.

        Possible exceptions: NotAvailable, JobFailed.
        See Page.get_info() for details.
        '''
        def __get__(self):
            self._get_info()
            return self.ddjvu_pageinfo.rotation * 90

    property version:
        '''
        Return the page version.

        Possible exceptions: NotAvailable, JobFailed.
        See Page.get_info() for details.
        '''
        def __get__(self):
            self._get_info()
            return self.ddjvu_pageinfo.version

    property dump:
        '''
        Return a text describing the contents of the page using the same format
        as the djvudump command.

        If the information is not available, raise NotAvailable exception.
        Then PageInfoMessage messages with empty page_job may be emitted.

        Possible exceptions: NotAvailable.
        '''
        def __get__(self):
            cdef char* s
            s = ddjvu_document_get_pagedump(self._document.ddjvu_document, self._n)
            if s == NULL:
                raise _NotAvailable_
            try:
                return decode_utf8(s)
            finally:
                libc_free(s)

    def decode(self, wait=1):
        '''
        P.decode(wait=True) -> a PageJob

        Initiate data transfer and decoding threads for the page.

        If wait is true, wait until the job is done.

        Possible exceptions:

        - NotAvailable (if called before receiving the DocInfoMessage).
        - JobFailed (if document decoding failed).
        '''
        cdef PageJob job
        cdef ddjvu_job_t* ddjvu_job
        with nogil: acquire_lock(loft_lock, WAIT_LOCK)
        try:
            ddjvu_job = <ddjvu_job_t*> ddjvu_page_create_by_pageno(self._document.ddjvu_document, self._n)
            if ddjvu_job == NULL:
                raise _NotAvailable_
            if ddjvu_document_decoding_error(self._document.ddjvu_document):
                raise JobException_from_c(ddjvu_document_decoding_status(self._document.ddjvu_document))
            job = PageJob(sentinel = the_sentinel)
            job.__init(self._document._context, ddjvu_job)
        finally:
            release_lock(loft_lock)
        if wait:
            job.wait()
        return job

    property annotations:
        '''
        Return PageAnnotations for the page.
        '''
        def __get__(self):
            return PageAnnotations(self)

    property text:
        '''
        Return PageText for the page.
        '''
        def __get__(self):
            return PageText(self)

    def __repr__(self):
        return '%s(%r, %r)' % (get_type_name(Page), self._document, self._n)

cdef class Thumbnail:

    '''
    Thumbnail for a page.

    Use page.thumbnail to obtain instances of this class.
    '''

    def __cinit__(self, Page page not None):
        self._page = page

    property page:
        '''
        Return the page.
        '''
        def __get__(self):
            return self._page

    property status:
        '''
        Determine whether the thumbnail is available. Return a JobException
        subclass indicating the current job status.
        '''
        def __get__(self):
            return JobException_from_c(ddjvu_thumbnail_status(self._page._document.ddjvu_document, self._page._n, 0))

    def calculate(self):
        '''
        T.calculate() -> a JobException

        Determine whether the thumbnail is available. If it's not, initiate the
        thumbnail calculating job. Regardless of its success, the completion of
        the job is signalled by a subsequent ThumbnailMessage.

        Return a JobException subclass indicating the current job status.
        '''
        return JobException_from_c(ddjvu_thumbnail_status(self._page._document.ddjvu_document, self._page._n, 1))

    def render(self, size, PixelFormat pixel_format not None, long row_alignment=1, dry_run=0, buffer=None):
        '''
        T.render((w0, h0), pixel_format, row_alignment=1, dry_run=False, buffer=None) -> ((w1, h1, row_size), data)

        Render the thumbnail:

        * not larger than w0 x h0 pixels;
        * using the pixel_format pixel format;
        * with each row starting at row_alignment bytes boundary;
        * into the provided buffer or to a newly created string.

        Raise NotAvailable when no thumbnail is available.
        Otherwise, return a ((w1, h1, row_size), data) tuple:

        * w1 and h1 are actual thumbnail dimensions in pixels
          (w1 <= w0 and h1 <= h0);
        * row_size is length of each image row, in bytes;
        * data is None if dry_run is true; otherwise is contains the
          actual image data.
        '''
        cdef int iw, ih
        cdef long w, h, row_size
        cdef void* memory
        if row_alignment <= 0:
            raise ValueError('row_alignment must be a positive integer')
        w, h = size
        if w <= 0 or h <= 0:
            raise ValueError('size width/height must a positive integer')
        iw, ih = w, h
        if iw != w or ih != h:
            raise OverflowError('size width/height is too large')
        row_size = calculate_row_size(w, row_alignment, pixel_format._bpp)
        if dry_run:
            result = None
            memory = NULL
        else:
            result = allocate_image_memory(row_size, h, buffer, &memory)
        if ddjvu_thumbnail_render(self._page._document.ddjvu_document, self._page._n, &iw, &ih, pixel_format.ddjvu_format, row_size, <char*> memory):
            return (iw, ih, row_size), result
        else:
            raise _NotAvailable_

    def __repr__(self):
        return '%s(%r)' % (get_type_name(Thumbnail), self._page)

cdef class DocumentFiles(DocumentExtension):

    '''
    Component files of a document.

    Use document.files to obtain instances of this class.

    File indexing is zero-based, i.e. files[0] stands for the very first file.

    len(files) might raise NotAvailable when called before receiving
    a DocInfoMessage.
    '''

    def __cinit__(self, Document document not None, **kwargs):
        check_sentinel(self, kwargs)
        self._page_map = None
        self._document = document

    def __len__(self):
        cdef int result
        result = ddjvu_document_get_filenum(self._document.ddjvu_document)
        if result is None:
            raise _NotAvailable_
        return result

    def __getitem__(self, key):
        cdef int i
        if is_int(key):
            if key < 0 or key >= len(self):
                raise IndexError('file number out of range')
            return File(self._document, key, sentinel = the_sentinel)
        elif typecheck(key, Page):
            if (<Page>key)._document is not self._document:
                raise KeyError(key)
            if self._page_map is None:
                self._page_map = {}
                for i from 0 <= i < len(self):
                    file = File(self._document, i, sentinel = the_sentinel)
                    n_page = file.n_page
                    if n_page is not None:
                        self._page_map[n_page] = file
            try:
                return self._page_map[(<Page>key)._n]
            except KeyError:
                raise KeyError(key)
        else:
            raise TypeError('DocumentFiles indices must be integers or Page instances')


cdef class File:

    '''
    Component file of a document.

    Use document.files[N] to obtain instances of this class.
    '''

    def __cinit__(self, Document document not None, int n, **kwargs):
        check_sentinel(self, kwargs)
        self._document = document
        self._have_info = 0
        self._n = n

    property document:
        '''Return the Document which includes the component file.'''
        def __get__(self):
            return self._document

    property n:
        '''
        Return the component file number.

        File indexing is zero-based, i.e. 0 stands for the very first file.
        '''
        def __get__(self):
            return self._n

    cdef object _get_info(self):
        cdef ddjvu_status_t status
        if self._have_info:
            return
        status = ddjvu_document_get_fileinfo(self._document.ddjvu_document, self._n, &self.ddjvu_fileinfo)
        ex = JobException_from_c(status)
        if ex is JobOK:
            return
        elif ex is JobStarted:
            raise _NotAvailable_
        else:
            raise ex

    def get_info(self, wait=1):
        '''
        F.get_info(wait=True) -> None

        Attempt to obtain information about the component file.

        If wait is true, wait until the information is available.

        Possible exceptions: NotAvailable, JobFailed.
        '''
        cdef ddjvu_status_t status
        if self._have_info:
            return
        if not wait:
            return self._get_info()
        while 1:
            self._document._condition.acquire()
            try:
                status = ddjvu_document_get_fileinfo(self._document.ddjvu_document, self._n, &self.ddjvu_fileinfo)
                ex = JobException_from_c(status)
                if ex is JobOK:
                    self._have_info = 1
                    return
                elif ex is JobStarted:
                    self._document._condition.wait()
                else:
                    raise ex
            finally:
                self._document._condition.release()

    property type:
        '''
        Return the type of the compound file:

        * FILE_TYPE_PAGE,
        * FILE_TYPE_THUMBNAILS,
        * FILE_TYPE_INCLUDE.

        Possible exceptions: NotAvailable, JobFailed.
        '''
        def __get__(self):
            cdef char buffer[2]
            self._get_info()
            buffer[0] = self.ddjvu_fileinfo.type
            buffer[1] = '\0'
            return charp_to_string(buffer)

    property n_page:
        '''
        Return the page number, or None when not applicable.

        Page indexing is zero-based, i.e. 0 stands for the very first page.

        Possible exceptions: NotAvailable, JobFailed.
        '''
        def __get__(self):
            self._get_info()
            if self.ddjvu_fileinfo.pageno < 0:
                return
            else:
                return self.ddjvu_fileinfo.pageno

    property page:
        '''
        Return the page, or None when not applicable.

        Possible exceptions: NotAvailable, JobFailed.
        '''
        def __get__(self):
            self._get_info()
            if self.ddjvu_fileinfo.pageno < 0:
                return
            else:
                return self._document.pages[self.ddjvu_fileinfo.pageno]

    property size:
        '''
        Return the compound file size, or None when unknown.

        Possible exceptions: NotAvailable, JobFailed.
        '''
        def __get__(self):
            self._get_info()
            if self.ddjvu_fileinfo.size < 0:
                return
            else:
                return self.ddjvu_fileinfo.size

    property id:
        '''
        Return the compound file identifier, or None.

        Possible exceptions: NotAvailable, JobFailed.
        '''
        def __get__(self):
            self._get_info()
            cdef char* result
            result = <char*> self.ddjvu_fileinfo.id
            if result == NULL:
                return
            else:
                return decode_utf8(result)

    property name:
        '''
        Return the compound file name, or None.

        Possible exceptions: NotAvailable, JobFailed.
        '''
        def __get__(self):
            self._get_info()
            cdef char* result
            result = <char*> self.ddjvu_fileinfo.name
            if result == NULL:
                return
            else:
                return decode_utf8(result)

    property title:
        '''
        Return the compound file title, or None.

        Possible exceptions: NotAvailable, JobFailed.
        '''
        def __get__(self):
            self._get_info()
            cdef char* result
            result = <char*> self.ddjvu_fileinfo.title
            if result == NULL:
                return
            else:
                return decode_utf8(result)


    property dump:
        '''
        Return a text describing the contents of the file using the same format
        as the djvudump command.

        If the information is not available, raise NotAvailable exception.
        Then, PageInfoMessage messages with empty page_job may be emitted.

        Possible exceptions: NotAvailable.
        '''
        def __get__(self):
            cdef char* s
            s = ddjvu_document_get_filedump(self._document.ddjvu_document, self._n)
            if s == NULL:
                raise _NotAvailable_
            try:
                return decode_utf8(s)
            finally:
                libc_free(s)

cdef object pages_to_opt(object pages, int sort_uniq):
    if sort_uniq:
        pages = sorted(frozenset(pages))
    else:
        pages = list(pages)
    for i from 0 <= i < len(pages):
        if not is_int(pages[i]):
            raise TypeError('page numbers must be integers')
        if pages[i] < 0:
            raise ValueError('page number out of range')
        pages[i] = pages[i] + 1
    result = '--pages=' + (','.join(imap(str, pages)))
    if is_unicode(result):
        result = encode_utf8(result)
    return result

PRINT_ORIENTATION_AUTO = None
PRINT_ORIENTATION_LANDSCAPE = 'landscape'
PRINT_ORIENTATION_PORTRAIT = 'portrait'

cdef object PRINT_RENDER_MODE_MAP
PRINT_RENDER_MODE_MAP = \
{
    DDJVU_RENDER_COLOR: None,
    DDJVU_RENDER_BLACK: 'bw',
    DDJVU_RENDER_FOREGROUND: 'fore',
    DDJVU_RENDER_BACKGROUND: 'back'
}

PRINT_BOOKLET_NO = None
PRINT_BOOKLET_YES = 'yes'
PRINT_BOOKLET_RECTO = 'recto'
PRINT_BOOKLET_VERSO = 'verso'

cdef object PRINT_BOOKLET_OPTIONS
PRINT_BOOKLET_OPTIONS = (PRINT_BOOKLET_NO, PRINT_BOOKLET_YES, PRINT_BOOKLET_RECTO, PRINT_BOOKLET_VERSO)

cdef class SaveJob(Job):

    '''
    Document saving job.

    Use document.save(...) to obtain instances of this class.
    '''

    def __cinit__(self, **kwargs):
        self._file = None

    def wait(self):
        Job.wait(self)
        # Ensure that the underlying file is flushed.
        # FIXME: In Python 3, the file might be never flushed if you don't use wait()!
        if self._file is not None:
            (<_FileWrapper> self._file).close()
            self._file = None

cdef class DocumentDecodingJob(Job):

    '''
    Document decoding job.

    Use document.decoding_job to obtain instances of this class.
    '''

    cdef object __init_ddj(self, Document document):
        self._context = document._context
        self._document = document
        self._condition = document._condition
        self._queue = document._queue
        self.ddjvu_job = <ddjvu_job_t*> document.ddjvu_document

    def __dealloc__(self):
        self.ddjvu_job = NULL # Don't allow Job.__dealloc__ to release the job.

    def __repr__(self):
        return '<%s for %r>' % (get_type_name(DocumentDecodingJob), self._document)

cdef class Document:

    '''
    DjVu document.

    Use context.new_document(...) to obtain instances of this class.
    '''

    def __cinit__(self, **kwargs):
        self.ddjvu_document = NULL
        check_sentinel(self, kwargs)
        self._pages = DocumentPages(self, sentinel = the_sentinel)
        self._files = DocumentFiles(self, sentinel = the_sentinel)
        self._context = None
        self._queue = Queue()
        self._condition = Condition()

    cdef object __init(self, Context context, ddjvu_document_t *ddjvu_document):
        # Assumption: loft_lock is already acquired.
        assert context != None and ddjvu_document != NULL
        self.ddjvu_document = ddjvu_document
        self._context = context
        _document_loft.add(self)
        _document_weak_loft[voidp_to_int(ddjvu_document)] = self

    cdef object __clear(self):
        with nogil: acquire_lock(loft_lock, WAIT_LOCK)
        try:
            _document_loft.discard(self)
        finally:
            release_lock(loft_lock)

    property decoding_status:
        '''
        Return a JobException subclass indicating the decoding job status.
        '''
        def __get__(self):
            return JobException_from_c(ddjvu_document_decoding_status(self.ddjvu_document))

    property decoding_error:
        '''
        Indicate whether the decoding job failed.
        '''
        def __get__(self):
            return bool(ddjvu_document_decoding_error(self.ddjvu_document))

    property decoding_done:
        '''
        Indicate whether the decoding job is done.
        '''
        def __get__(self):
            return bool(ddjvu_document_decoding_done(self.ddjvu_document))

    property decoding_job:
        '''
        Return the DocumentDecodingJob.
        '''
        def __get__(self):
            cdef DocumentDecodingJob job
            job = DocumentDecodingJob(sentinel = the_sentinel)
            job.__init_ddj(self)
            return job

    property type:
        '''
        Return the type of the document.

        The following values are possible:
        * DOCUMENT_TYPE_UNKNOWN;
        * DOCUMENT_TYPE_SINGLE_PAGE: single-page document;
        * DOCUMENT_TYPE_BUNDLED: bundled mutli-page document;
        * DOCUMENT_TYPE_INDIRECT: indirect multi-page document;
        * (obsolete) DOCUMENT_TYPE_OLD_BUNDLED,
        * (obsolete) DOCUMENT_TYPE_OLD_INDEXED.

        Before receiving the DocInfoMessage, DOCUMENT_TYPE_UNKNOWN may be returned.
        '''
        def __get__(self):
            return ddjvu_document_get_type(self.ddjvu_document)

    property pages:
        '''
        Return the DocumentPages.
        '''
        def __get__(self):
            return self._pages

    property files:
        '''
        Return the DocumentPages.
        '''
        def __get__(self):
            return self._files

    property outline:
        '''
        Return the DocumentOutline.
        '''
        def __get__(self):
            return DocumentOutline(self)

    property annotations:
        '''
        Return the DocumentAnnotations.
        '''
        def __get__(self):
            return DocumentAnnotations(self)

    def __dealloc__(self):
        if self.ddjvu_document == NULL:
            return
        ddjvu_document_release(self.ddjvu_document)

    def save(self, file=None, indirect=None, pages=None, wait=1):
        '''
        D.save(file=None, indirect=None, pages=<all-pages>, wait=True) -> a SaveJob

        Save the document as:

        * a bundled DjVu file or;
        * an indirect DjVu document with index file name indirect.

        pages argument specifies a subset of saved pages.

        If wait is true, wait until the job is done.

        .. warning::
            Due to a DjVuLibre (<= 3.5.20) bug, this method may be broken.
            See http://bugs.debian.org/467282 for details.
        '''
        cdef char * optv[2]
        cdef int optc
        cdef SaveJob job
        optc = 0
        cdef FILE* output
        cdef Py_ssize_t i
        cdef _FileWrapper file_wrapper
        if indirect is None:
            file_wrapper = _FileWrapper(file, <char*> "wb")
            output = file_wrapper.cfile
        else:
            if file is not None:
                raise TypeError('file must be None if indirect is specified')
            if not is_string(indirect):
                raise TypeError('indirect must be a string')
            # XXX ddjvu API documentation says that output should be NULL,
            # but we'd like to spot the DjVuLibre bug
            open(indirect, 'wb').close()
            file = open(devnull, 'wb')
            file_wrapper = _FileWrapper(file, <char*> "wb")
            output = file_wrapper.cfile
            s1 = '--indirect=' + indirect
            if is_unicode(s1):
                s1 = encode_utf8(s1)
            optv[optc] = s1
            optc = optc + 1
        if pages is not None:
            s2 = pages_to_opt(pages, 1)
            optv[optc] = s2
            optc = optc + 1
        with nogil: acquire_lock(loft_lock, WAIT_LOCK)
        try:
            job = SaveJob(sentinel = the_sentinel)
            job.__init(self._context, ddjvu_document_save(self.ddjvu_document, output, optc, optv))
            job._file = file_wrapper
        finally:
            release_lock(loft_lock)
        if wait:
            job.wait()
            if indirect is not None:
                file = open(indirect, 'rb')
                file.seek(0, 2)
            if file.tell() == 0:
                raise DjVuLibreBug(467282)
        return job

    def export_ps(self, file, pages=None, eps=0, level=None, orientation=PRINT_ORIENTATION_AUTO, mode=DDJVU_RENDER_COLOR, zoom=None, color=1, srgb=1, gamma=None, copies=1, frame=0, crop_marks=0, text=0, booklet=PRINT_BOOKLET_NO, booklet_max=0, booklet_align=0, booklet_fold=(18, 200), wait=1):
        '''
        D.export_ps(file, pages=<all-pages>, ..., wait=True) -> a Job

        Convert the document into PostScript.

        pages argument specifies a subset of saved pages.

        If wait is true, wait until the job is done.

        Additional options
        ------------------

        eps
            Produce an *Encapsulated* PostScript file. Encapsulated PostScript
            files are suitable for embedding images into other documents.
            Encapsulated PostScript file can only contain a single page.
            Setting this option overrides the options copies, orientation,
            zoom, crop_marks, and booklet.
        level
            Selects the language level of the generated PostScript. Valid
            language levels are 1, 2, and 3. Level 3 produces the most compact
            and fast printing PostScript files. Some of these files however
            require a very modern printer. Level 2 is the default value. The
            generated PostScript files are almost as compact and work with all
            but the oldest PostScript printers. Level 1 can be used as a last
            resort option.
        orientation
            Specifies the pages orientation:
            PRINT_ORIENTATION_AUTO
                automatic
            PRINT_ORIENTATION_PORTRAIT
                portrait
            PRINT_ORIENTATION_LANDSCAPE
                landscape
        mode
            Specifies how pages should be decoded:
            RENDER_COLOR
                render all the layers of the DjVu documents
            RENDER_BLACK
                render only the foreground layer mask
            RENDER_FOREGROUND
                render only the foreground layer
            RENDER_BACKGROUND
                redner only the background layer
        zoom
            Specifies a zoom factor. The default zoom factor scales the image to
            fit the page.
        color
            Specifies whether to generate a color or a gray scale PostScript
            file. A gray scale PostScript files are smaller and marginally more
            portable.
        srgb
            The default value, True, generates a PostScript file using device
            independent colors in compliance with the sRGB specification.
            Modern printers then produce colors that match the original as well
            as possible. Specifying a false value generates a PostScript file
            using device dependent colors. This is sometimes useful with older
            printers. You can then use the gamma option to tune the output
            colors.
        gamma
            Specifies a gamma correction factor for the device dependent
            PostScript colors. Argument must be in range 0.3 to 5.0. Gamma
            correction normally pertains to cathodic screens only. It gets
            meaningful for printers because several models interpret device
            dependent RGB colors by emulating the color response of a cathodic
            tube.
        copies
            Specifies the number of copies to print.
        frame,
            If true, generate a thin gray border representing the boundaries of
            the document pages.
        crop_marks
            If true, generate crop marks indicating where pages should be cut.
        text
            Generate hidden text. This option is deprecated. See also the
            warning below.
        booklet
            * PRINT_BOOKLET_NO
                Disable booklet mode. This is the default.
            * PRINT_BOOKLET_YES:
                Enable recto/verse booklet mode.
            * PRINT_BOOKLET_RECTO
                Enable recto booklet mode.
            * PRINT_BOOKLET_VERSO
                Enable verso booklet mode.
        booklet_max
            Specifies the maximal number of pages per booklet. A single printout
            might then be composed of several booklets. The argument is rounded
            up to the next multiple of 4. Specifying 0 sets no maximal number
            of pages and ensures that the printout will produce
            a single booklet. This is the default.
        booklet_align
            Specifies a positive or negative offset applied to the verso of
            each sheet. The argument is expressed in points[1]_. This is useful
            with certain printers to ensure that both recto and verso are
            properly aligned. The default value is 0.
        booklet_fold (= (base, increment))
            Specifies the extra margin left between both pages on a single
            sheet. The base value is expressed in points[1]_. This margin is
            incremented for each outer sheet by value expressed in millipoints.
            The default value is (18, 200).

        .. [1] 1 pt = 1/72 in = 0.3528 mm

        **Warning***
        ------------
        Due to a DjVuLibre (<= 3.5.20) bug, this method may be broken.
        See http://bugs.debian.org/469122 for details.
        '''
        cdef FILE* output
        cdef SaveJob job
        cdef _FileWrapper file_wrapper
        options = []
        file_wrapper = _FileWrapper(file, <char*> "wb")
        output = file_wrapper.cfile
        if pages is not None:
            list_append(options, pages_to_opt(pages, 0))
        if eps:
            list_append(options, '--format=eps')
        if level is not None:
            if not is_int(level):
                raise TypeError('level must be an integer')
            list_append(options, '--level=%d' % level)
        if orientation is not None:
            if not is_string(orientation):
                raise TypeError('orientation must be a string or none')
            list_append(options, '--orientation=' + orientation)
        if not is_int(mode):
            raise TypeError('mode must be an integer')
        try:
            mode = PRINT_RENDER_MODE_MAP[mode]
            if mode is not None:
                list_append(options, '--mode=' + mode)
        except KeyError:
            raise ValueError('mode must be equal to RENDER_COLOR, or RENDER_BLACK, or RENDER_FOREGROUND, or RENDER_BACKGROUND')
        if zoom is not None:
            if not is_int(zoom):
                raise TypeError('zoom must be an integer or none')
            list_append(options, '--zoom=%d' % zoom)
        if not color:
            list_append(options, '--color=no')
        if not srgb:
            list_append(options, '--srgb=no')
        if gamma is not None:
            if not is_int(gamma) and not is_float(gamma):
                raise TypeError('gamma must be a number or none')
            list_append(options, '--gamma=%.16f' % gamma)
        if not is_int(copies):
            raise TypeError('copies must be an integer')
        if copies != 1:
            list_append(options, '--options=%d' % copies)
        if frame:
            list_append(options, '--frame')
        if crop_marks:
            list_append(options, '--cropmarks')
        if text:
            list_append(options, '--text')
        if booklet is not None:
            if not is_string(booklet):
                raise TypeError('booklet must be a string or none')
            if options not in PRINT_BOOKLET_OPTIONS:
                raise ValueError('booklet must be equal to PRINT_BOOKLET_NO, or PRINT_BOOKLET_YES, or PRINT_BOOKLET_VERSO, or PRINT_BOOKLET_RECTO')
            list_append(options, '--booklet=' + booklet)
        if not is_int(booklet_max):
            raise TypeError('booklet_max must be an integer')
        if booklet_max:
            list_append(options, '--bookletmax=%d' % booklet_max)
        if not is_int(booklet_align):
            raise TypeError('booklet_align must be an integer')
        if booklet_align:
            list_append(options, '--bookletalign=%d' % booklet_align)
        if is_int(booklet_fold):
            list_append(options, '--bookletfold=%d' % booklet_fold)
        else:
            try:
                fold_base, fold_incr = booklet_fold
                if not is_int(fold_base) or not is_int(fold_incr):
                    raise TypeError
            except TypeError:
                raise TypeError('booklet_fold must a be an integer or a pair of integers')
            list_append(options, '--bookletfold=%d+%d' % (fold_base, fold_incr))
        cdef char **optv
        cdef int optc
        cdef size_t buffer_size
        optc = 0
        buffer_size = len(options) * sizeof (char*)
        optv = <char**> py_malloc(buffer_size)
        if optv == NULL:
            raise MemoryError('Unable to allocate %d bytes for print options' % buffer_size)
        try:
            for optc from 0 <= optc < len(options):
                option = options[optc]
                if is_unicode(option):
                    options[optc] = option = encode_utf8(option)
                optv[optc] = option
            assert optc == len(options)
            with nogil: acquire_lock(loft_lock, WAIT_LOCK)
            try:
                job = SaveJob(sentinel = the_sentinel)
                job.__init(self._context, ddjvu_document_print(self.ddjvu_document, output, optc, optv))
                job._file = file_wrapper
            finally:
                release_lock(loft_lock)
        finally:
            py_free(optv)
        if wait:
            job.wait()
        return job

    property message_queue:
        '''
        Return the internal message queue.
        '''
        def __get__(self):
            return self._queue

    def get_message(self, wait=1):
        '''
        D.get_message(wait=True) -> a Message or None

        Get message from the internal document queue.
        Return None if wait is false and no message is available.
        '''
        try:
            return self._queue.get(wait)
        except Empty:
            return

    def __iter__(self):
        return self

    def __next__(self):
        return self.get_message()

cdef Document Document_from_c(ddjvu_document_t* ddjvu_document):
    cdef Document result
    if ddjvu_document == NULL:
        result = None
    else:
        with nogil: acquire_lock(loft_lock, WAIT_LOCK)
        try:
            result = _document_weak_loft.get(voidp_to_int(ddjvu_document))
        finally:
            release_lock(loft_lock)
    return result


class FileUri(str):
    '''
    See the Document.new_document() method.
    '''

FileURI = FileUri

cdef object Context_message_distributor
def _Context_message_distributor(Context self not None, **kwargs):
    cdef Message message
    cdef Document document
    cdef Job job
    cdef PageJob page_job
    cdef ddjvu_message_t* ddjvu_message

    check_sentinel(self, kwargs)
    while 1:
        with nogil:
            ddjvu_message = ddjvu_message_wait(self.ddjvu_context)
        try:
            try:
                message = Message_from_c(ddjvu_message)
            finally:
                ddjvu_message_pop(self.ddjvu_context)
            if message is None:
                raise SystemError
            self.handle_message(message)
            # XXX Order of branches below is *crucial*. Do not change.
            if message._job is not None:
                job = message._job
                job._condition.acquire()
                try:
                    job._condition.notifyAll()
                finally:
                    job._condition.release()
                if job.is_done:
                    job.__clear()
            elif message._page_job is not None:
                raise SystemError # should not happen
            elif message._document is not None:
                document = message._document
                document._condition.acquire()
                try:
                    document._condition.notifyAll()
                finally:
                    document._condition.release()
                if document.decoding_done:
                    document.__clear()
        except KeyboardInterrupt:
            return
        except SystemExit:
            return
        except Exception:
            write_unraisable_exception(self)
Context_message_distributor = _Context_message_distributor
del _Context_message_distributor

cdef class Context:

    def __cinit__(self, argv0=None):
        if argv0 is None:
            argv0 = sys.argv[0]
        if is_unicode(argv0):
            argv0 = encode_utf8(argv0)
        with nogil: acquire_lock(loft_lock, WAIT_LOCK)
        try:
            self.ddjvu_context = ddjvu_context_create(argv0)
            if self.ddjvu_context == NULL:
                raise MemoryError('Unable to create DjVu context')
            _context_loft[voidp_to_int(self.ddjvu_context)] = self
        finally:
            release_lock(loft_lock)
        self._queue = Queue()
        thread.start_new_thread(Context_message_distributor, (self,), {'sentinel': the_sentinel})

    property cache_size:

        def __set__(self, value):
            if 0 < value < (1 << 31):
                ddjvu_cache_set_size(self.ddjvu_context, value)
            else:
                raise ValueError('0 < cache_size < (2 ** 31) must be satisfied')

        def __get__(self):
            return ddjvu_cache_get_size(self.ddjvu_context)

    def handle_message(self, Message message not None):
        '''
        C.handle_message(message) -> None

        This method is called, in a separate thread, for every received
        message, *before* any blocking method finishes.

        By default do something roughly equivalent to::

            if message.job is not None:
                message.job.message_queue.put(message)
            elif message.document is not None:
                message.document.message_queue.put(message)
            else:
                message.context.message_queue.put(message)

        You may want to override this method to change this behaviour.

        All exceptions raised by this method will be ignored.
        '''

        # XXX Order of branches below is *crucial*. Do not change.
        if message._job is not None:
            message._job._queue.put(message)
        elif message._page_job is not None:
            raise SystemError # should not happen
        elif message._document is not None:
            message._document._queue.put(message)
        else:
            message._context._queue.put(message)

    property message_queue:
        '''
        Return the internal message queue.
        '''
        def __get__(self):
            return self._queue

    def get_message(self, wait=1):
        '''
        C.get_message(wait=True) -> a Message or None

        Get message from the internal context queue.
        Return None if wait is false and no message is available.
        '''
        try:
            return self._queue.get(wait)
        except Empty:
            return

    def new_document(self, uri, cache=1):
        '''
        C.new_document(uri, cache=True) -> a Document

        Creates a decoder for a DjVu document and starts decoding. This
        method returns immediately. The decoding job then generates messages to
        request the raw data and to indicate the state of the decoding process.

        uri specifies an optional URI for the document. The URI follows the
        usual syntax (protocol://machine/path). It should not end with
        a slash. It only serves two purposes:

        - The URI is used as a key for the cache of decoded pages.
        - The URI is used to document NewStreamMessage messages.

        Setting argument cache to a true vaule indicates that decoded pages
        should be cached when possible.

        It is important to understand that the URI is not used to access the
        data. The document generates NewStreamMessage messages to indicate
        which data is needed. The caller must then provide the raw data using
        a NewStreamMessage.stream object.

        To open a local file, provide a FileUri instance as an uri.

        Localized characters in uri should be in URI-encoded.

        Possible exceptions: JobFailed.
        '''
        cdef Document document
        cdef ddjvu_document_t* ddjvu_document
        with nogil: acquire_lock(loft_lock, WAIT_LOCK)
        try:
            if typecheck(uri, FileUri):
                IF PY3K:
                    uri = encode_utf8(uri)
                ddjvu_document = ddjvu_document_create_by_filename(self.ddjvu_context, uri, cache)
            else:
                IF PY3K:
                    uri = encode_utf8(uri)
                ddjvu_document = ddjvu_document_create(self.ddjvu_context, uri, cache)
            if ddjvu_document == NULL:
                raise JobFailed
            document = Document(sentinel = the_sentinel)
            document.__init(self, ddjvu_document)
        finally:
            release_lock(loft_lock)
        return document

    def __iter__(self):
        return self

    def __next__(self):
        return self.get_message()

    def clear_cache(self):
        '''
        C.clear_cache() -> None
        '''
        ddjvu_cache_clear(self.ddjvu_context)

    def __dealloc__(self):
        ddjvu_context_release(self.ddjvu_context)

cdef Context Context_from_c(ddjvu_context_t* ddjvu_context):
    cdef Context result
    if ddjvu_context == NULL:
        result = None
    else:
        with nogil: acquire_lock(loft_lock, WAIT_LOCK)
        try:
            try:
                result = _context_loft[voidp_to_int(ddjvu_context)]
            except KeyError:
                raise SystemError
        finally:
            release_lock(loft_lock)
    return result

RENDER_COLOR = DDJVU_RENDER_COLOR
RENDER_BLACK = DDJVU_RENDER_BLACK
RENDER_COLOR_ONLY = DDJVU_RENDER_COLORONLY
RENDER_MASK_ONLY = DDJVU_RENDER_MASKONLY
RENDER_BACKGROUND = DDJVU_RENDER_BACKGROUND
RENDER_FOREGROUND = DDJVU_RENDER_FOREGROUND

PAGE_TYPE_UNKNOWN = DDJVU_PAGETYPE_UNKNOWN
PAGE_TYPE_BITONAL = DDJVU_PAGETYPE_BITONAL
PAGE_TYPE_PHOTO = DDJVU_PAGETYPE_PHOTO
PAGE_TYPE_COMPOUND = DDJVU_PAGETYPE_COMPOUND

cdef class PixelFormat:

    '''
    Abstract pixel format.

    Don't use this class directly, use one of its subclasses.
    '''

    def __cinit__(self, *args, **kwargs):
        self._row_order = 0
        self._y_direction = 0
        self._dither_bpp = 32
        self._gamma = 2.2
        self.ddjvu_format = NULL
        for cls in (PixelFormatRgb, PixelFormatRgbMask, PixelFormatGrey, PixelFormatPalette, PixelFormatPackedBits):
            if typecheck(self, cls):
                return
        raise_instantiation_error(type(self))

    property rows_top_to_bottom:
        '''
        Flag indicating whether the rows in the pixel buffer are stored
        starting from the top or the bottom of the image.

        Default ordering starts from the bottom of the image. This is the
        opposite of the X11 convention.
        '''

        def __get__(self):
            return bool(self._row_order)

        def __set__(self, value):
            ddjvu_format_set_row_order(self.ddjvu_format, not not value)

    property y_top_to_bottom:
        '''
        Flag indicating whether the *y* coordinates in the drawing area are
        oriented from bottom to top, or from top to bottom.

        The default is bottom to top, similar to PostScript. This is the
        opposite of the X11 convention.
        '''

        def __get__(self):
            return bool(self._row_order)

        def __set__(self, value):
            ddjvu_format_set_y_direction(self.ddjvu_format, not not value)

    property bpp:
        '''
        Return the depth of the image, in bits per pixel.
        '''
        def __get__(self):
            return self._bpp

    property dither_bpp:
        '''
        The final depth of the image on the screen. This is used to decide
        which dithering algorithm should be used.

        The default is usually appropriate.
        '''
        def __get__(self):
            return self._dither_bpp

        def __set__(self, int value):
            if (0 < value < 64):
                ddjvu_format_set_ditherbits(self.ddjvu_format, value)
                self._dither_bpp = value
            else:
                raise ValueError('0 < value < 64 must be satisfied')

    property gamma:
        '''
        Gamma of the display for which the pixels are intended. This will be
        combined with the gamma stored in DjVu documents in order to compute
        a suitable color correction.

        The default value is 2.2.
        '''
        def __get__(self):
            return self._gamma

        def __set__(self, double value):
            if (0.5 <= value <= 5.0):
                ddjvu_format_set_gamma(self.ddjvu_format, value)
            else:
                raise ValueError('0.5 <= value <= 5.0 must be satisfied')

    def __dealloc__(self):
        if self.ddjvu_format != NULL:
            ddjvu_format_release(self.ddjvu_format)

    def __repr__(self):
        return '%s()' % (get_type_name(type(self)),)

cdef class PixelFormatRgb(PixelFormat):

    '''
    PixelFormatRgb([byteorder='RGB']) -> a pixel format

    24-bit pixel format, with:

    - RGB (byteorder == 'RGB') or
    - BGR (byteorder == 'BGR')

    byte order.
    '''

    def __cinit__(self, byte_order='RGB', unsigned int bpp=24):
        cdef unsigned int _format
        if byte_order == 'RGB':
            self._rgb = 1
            _format = DDJVU_FORMAT_RGB24
        elif byte_order == 'BGR':
            self._rgb = 0
            _format = DDJVU_FORMAT_BGR24
        else:
            raise ValueError("byte_order must be equal to 'RGB' or 'BGR'")
        if bpp != 24:
            raise ValueError('bpp must be equal to 24')
        self._bpp = 24
        self.ddjvu_format = ddjvu_format_create(_format, 0, NULL)

    property byte_order:
        '''
        Return the byte order:
        - 'RGB' or
        - 'BGR'.
        '''
        def __get__(self):
            if self._rgb:
                return 'RGB'
            else:
                return 'BGR'

    def __repr__(self):
        return '%s(byte_order = %r, bpp = %d)' % \
        (
            get_type_name(PixelFormatRgb),
            self.byte_order,
            self.bpp
        )

cdef class PixelFormatRgbMask(PixelFormat):

    '''
    PixelFormatRgbMask(red_mask, green_mask, blue_mask[, xor_value], bpp=16) -> a pixel format
    PixelFormatRgbMask(red_mask, green_mask, blue_mask[, xor_value], bpp=32) -> a pixel format

    red_mask, green_mask and blue_mask are bit masks for color components
    for each pixel. The resulting color is then xored with the xor_value.

    For example, PixelFormatRgbMask(0xf800, 0x07e0, 0x001f, bpp=16) is a
    highcolor format with:

    - 5 (most significant) bits for red,
    - 6 bits for green,
    - 5 (least significant) bits for blue.
    '''

    def __cinit__(self, unsigned int red_mask, unsigned int green_mask, unsigned int blue_mask, unsigned int xor_value = 0, unsigned int bpp = 16):
        cdef unsigned int _format
        if bpp == 16:
            _format = DDJVU_FORMAT_RGBMASK16
            red_mask = red_mask & 0xffff
            blue_mask = blue_mask & 0xffff
            green_mask = green_mask & 0xffff
            xor_value = xor_value & 0xffff
        elif bpp == 32:
            _format = DDJVU_FORMAT_RGBMASK32
            red_mask = red_mask & 0xffffffff
            blue_mask = blue_mask & 0xffffffff
            green_mask = green_mask & 0xffffffff
            xor_value = xor_value & 0xffffffff
        else:
            raise ValueError('bpp must be equal to 16 or 32')
        self._bpp = self._dither_bpp = bpp
        (self._params[0], self._params[1], self._params[2], self._params[3]) = (red_mask, green_mask, blue_mask, xor_value)
        self.ddjvu_format = ddjvu_format_create(_format, 4, self._params)

    def __repr__(self):
        return '%s(red_mask = 0x%0*x, green_mask = 0x%0*x, blue_mask = 0x%0*x, xor_value = 0x%0*x, bpp = %d)' % \
        (
            get_type_name(PixelFormatRgbMask),
            self.bpp//4, self._params[0],
            self.bpp//4, self._params[1],
            self.bpp//4, self._params[2],
            self.bpp//4, self._params[3],
            self.bpp,
        )

cdef class PixelFormatGrey(PixelFormat):

    '''
    PixelFormatGrey() -> a pixel format

    8-bit, grey pixel format.
    '''

    def __cinit__(self, unsigned int bpp = 8):
        cdef unsigned int params[4]
        if bpp != 8:
            raise ValueError('bpp must be equal to 8')
        self._bpp = self._dither_bpp = bpp
        self.ddjvu_format = ddjvu_format_create(DDJVU_FORMAT_GREY8, 0, NULL)

    def __repr__(self):
        return '%s(bpp = %d)' % (get_type_name(PixelFormatGrey), self.bpp)

cdef class PixelFormatPalette(PixelFormat):

    '''
    PixelFormatPalette(palette) -> a pixel format

    Palette pixel format.

    palette must be a dictionary which contains 216 (6 * 6 * 6) entries of
    a web color cube, such that:

    - for each key (r, g, b): r in range(0, 6), g in range(0, 6) etc.;
    - for each value v: v in range(0, 0x100).
    '''

    def __cinit__(self, palette, unsigned int bpp = 8):
        cdef int i, j, k, n
        for i from 0 <= i < 6:
            for j from 0 <= j < 6:
                for k from 0 <= k < 6:
                    n = palette[(i, j, k)]
                    if not 0 <= n < 0x100:
                        raise ValueError('palette entries must be in range(0, 0x100)')
                    self._palette[i*6*6 + j*6 + k] = n
        if bpp != 8:
            raise ValueError('bpp must be equal to 8')
        self._bpp = self._dither_bpp = bpp
        self.ddjvu_format = ddjvu_format_create(DDJVU_FORMAT_PALETTE8, 216, self._palette)

    def __repr__(self):
        cdef int i
        io = StringIO()
        io.write('%s({' % (get_type_name(PixelFormatPalette),))
        for i from 0 <= i < 6:
            for j from 0 <= j < 6:
                for k from 0 <= k < 6:
                    io.write('(%d, %d, %d): 0x%02x' % (i, j, k, self._palette[i * 6 * 6 + j * 6 + k]))
                    if not (i == j == k == 5):
                        io.write(', ')
        io.write('}, bpp = %d)' % self.bpp)
        return io.getvalue()

cdef class PixelFormatPackedBits(PixelFormat):

    '''
    PixelFormatPackedBits(endianness) -> a pixel format

    Bitonal, 1 bit per pixel format with:

    - most significant bits on the left (endianness=='>') or
    - least significant bits on the left (endianness=='<').
    '''

    def __cinit__(self, endianness):
        cdef int _format
        if endianness == '<':
            self._little_endian = 1
            _format = DDJVU_FORMAT_LSBTOMSB
        elif endianness == '>':
            self._little_endian = 0
            _format = DDJVU_FORMAT_MSBTOLSB
        else:
            raise ValueError("endianness must be equal to '<' or '>'")
        self._bpp = 1
        self._dither_bpp = 1
        self.ddjvu_format = ddjvu_format_create(_format, 0, NULL)

    property endianness:
        '''
        The endianness:
        - '<' (most significant bits on the left) or
        - '>' (least significant bits on the left).
        '''
        def __get__(self):
            if self._little_endian:
                return '<'
            else:
                return '>'

    def __repr__(self):
        return '%s(%r)' % (get_type_name(PixelFormatPackedBits), self.endianness)

cdef object calculate_row_size(long width, long row_alignment, int bpp):
    cdef long result
    cdef object row_size
    if bpp == 1:
        row_size = (width >> 3) + ((width & 7) != 0)
    elif bpp & 7 == 0:
        row_size = width
        row_size = row_size * (bpp >> 3)
    else:
        raise SystemError
    result = ((row_size + (row_alignment - 1)) / row_alignment) * row_alignment
    return result

cdef object allocate_image_memory(long width, long height, object buffer, void **memory):
    cdef Py_ssize_t c_requested_size
    cdef Py_ssize_t c_memory_size
    py_requested_size = int(width) * int(height)
    try:
        c_requested_size = py_requested_size
    except OverflowError:
        raise MemoryError('Unable to allocate %d bytes for an image memory' % py_requested_size)
    if buffer is None:
        result = charp_to_bytes(NULL, c_requested_size)
        memory[0] = <char*> result
    else:
        result = buffer
        buffer_to_writable_memory(buffer, memory, &c_memory_size)
        if c_memory_size < c_requested_size:
            raise ValueError('Image buffer is too small (%d > %d)' % (c_requested_size, c_memory_size))
    return result


cdef class PageJob(Job):

    '''
    A page decoding job.

    Use page.decode(...) to obtain instances of this class.
    '''

    cdef object __init(self, Context context, ddjvu_job_t *ddjvu_job):
        Job.__init(self, context, ddjvu_job)

    property width:
        '''
        Return the page width in pixels.

        Possible exceptions: NotAvailable (before receiving a
        PageInfoMessage).
        '''
        def __get__(self):
            cdef int width
            width = ddjvu_page_get_width(<ddjvu_page_t*> self.ddjvu_job)
            if width == 0:
                raise _NotAvailable_
            else:
                return width

    property height:
        '''
        Return the page height in pixels.

        Possible exceptions: NotAvailable (before receiving
        a PageInfoMessage).
        '''
        def __get__(self):
            cdef int height
            height = ddjvu_page_get_height(<ddjvu_page_t*> self.ddjvu_job)
            if height == 0:
                raise _NotAvailable_
            else:
                return height

    property size:
        '''
        page_job.size == (page_job.width, page_job.height)

        Possible exceptions: NotAvailable (before receiving
        a PageInfoMessage).
        '''
        def __get__(self):
            cdef int width
            cdef int height
            width = ddjvu_page_get_width(<ddjvu_page_t*> self.ddjvu_job)
            height = ddjvu_page_get_height(<ddjvu_page_t*> self.ddjvu_job)
            if width == 0 or height == 0:
                raise _NotAvailable_
            else:
                return width, height

    property dpi:
        '''
        Return the page resolution in pixels per inch.

        Possible exceptions: NotAvailable (before receiving
        a PageInfoMessage).
        '''
        def __get__(self):
            cdef int dpi
            dpi = ddjvu_page_get_resolution(<ddjvu_page_t*> self.ddjvu_job)
            if dpi == 0:
                raise _NotAvailable_
            else:
                return dpi

    property gamma:
        '''
        Return the gamma of the display for which this page was designed.

        Possible exceptions: NotAvailable (before receiving
        a PageInfoMessage).
        '''
        def __get__(self):
            return ddjvu_page_get_gamma(<ddjvu_page_t*> self.ddjvu_job)

    property version:
        '''
        Return the version of the DjVu file format.

        Possible exceptions: NotAvailable (before receiving
        a PageInfoMessage).
        '''
        def __get__(self):
            return ddjvu_page_get_version(<ddjvu_page_t*> self.ddjvu_job)

    property type:
        '''
        Return the type of the page data. Possible values are:

        * PAGE_TYPE_UNKNOWN,
        * PAGE_TYPE_BITONAL,
        * PAGE_TYPE_PHOTO,
        * PAGE_TYPE_COMPOUND.

        Possible exceptions: NotAvailable (before receiving
        a PageInfoMessage).
        '''
        def __get__(self):
            cdef ddjvu_page_type_t type
            cdef int is_done
            is_done = self.is_done
            type = ddjvu_page_get_type(<ddjvu_page_t*> self.ddjvu_job)
            if <int> type == <int> DDJVU_PAGETYPE_UNKNOWN and not is_done:
                # XXX An unavoidable race condition
                raise _NotAvailable_
            return type

    property initial_rotation:
        '''
        Return the counter-clockwise page rotation angle (in degrees)
        specified by the orientation flags in the DjVu file.

        Brain damage warning
        --------------------
        This is useful because maparea coordinates in the annotation chunks
        are expressed relative to the rotated coordinates whereas text
        coordinates in the hidden text data are expressed relative to the
        unrotated coordinates.
        '''
        def __get__(self):
            return 90 * <int> ddjvu_page_get_initial_rotation(<ddjvu_page_t*> self.ddjvu_job)

    property rotation:
        '''
        Return the counter-clockwise rotation angle (in degrees) for the page.
        The rotation is automatically taken into account by render(...)
        method and width and height properties.
        '''
        def __get__(self):
            return 90 * <int> ddjvu_page_get_rotation(<ddjvu_page_t*> self.ddjvu_job)

        def __set__(self, int value):
            cdef ddjvu_page_rotation_t rotation
            if value == 0:
                rotation = DDJVU_ROTATE_0
            elif value == 90:
                rotation = DDJVU_ROTATE_90
            elif value == 180:
                rotation = DDJVU_ROTATE_180
            elif value == 270:
                rotation = DDJVU_ROTATE_180
            else:
                raise ValueError('rotation must be equal to 0, 90, 180, or 270')
            ddjvu_page_set_rotation(<ddjvu_page_t*> self.ddjvu_job, rotation)

        def __del__(self):
            ddjvu_page_set_rotation(<ddjvu_page_t*> self.ddjvu_job, ddjvu_page_get_initial_rotation(<ddjvu_page_t*> self.ddjvu_job))

    def render(self, int mode, page_rect, render_rect, PixelFormat pixel_format not None, long row_alignment=1, buffer=None):
        '''
        J.render(mode, page_rect, render_rect, pixel_format, row_alignment=1, buffer=None) -> data

        Render a segment of a page with arbitrary scale. mode indicates
        which image layers should be rendered:

        RENDER_COLOR
            color page or stencil
        RENDER_BLACK
            stencil or color page
        RENDER_COLOR_ONLY
            color page or fail
        RENDER_MASK_ONLY
            stencil or fail
        RENDER_BACKGROUND
            color background layer
        RENDER_FOREGROUND
            color foreground layer

        Conceptually this method renders the full page into a rectangle
        page_rect and copies the pixels specified by rectangle
        render_rect into a buffer. The actual code is much more efficient
        than that.

        pixel_format specifies the expected pixel format. Each row will start
        at row_alignment bytes boundary.

        Data will be saved to the provided buffer or to a newly created string.

        This method makes a best effort to compute an image that reflects the
        most recently decoded data.

        Possible exceptions: NotAvailable (to indicate that no image could be
        computed at this point.)
        '''
        cdef ddjvu_rect_t c_page_rect
        cdef ddjvu_rect_t c_render_rect
        cdef Py_ssize_t buffer_size
        cdef long row_size
        cdef int bpp
        cdef long x, y, w, h
        cdef void *memory
        if row_alignment <= 0:
            raise ValueError('row_alignment must be a positive integer')
        x, y, w, h = page_rect
        if w <= 0 or h <= 0:
            raise ValueError('page_rect width/height must be a positive integer')
        c_page_rect.x, c_page_rect.y, c_page_rect.w, c_page_rect.h = x, y, w, h
        if c_page_rect.x != x or c_page_rect.y != y or c_page_rect.w != w or c_page_rect.h != h:
            raise OverflowError('render_rect coordinates are too large')
        x, y, w, h = render_rect
        if w <= 0 or h <= 0:
            raise ValueError('render_rect width/height must be a positive integer')
        c_render_rect.x, c_render_rect.y, c_render_rect.w, c_render_rect.h = x, y, w, h
        if c_render_rect.x != x or c_render_rect.y != y or c_render_rect.w != w or c_render_rect.h != h:
            raise OverflowError('render_rect coordinates are too large')
        if (
            c_page_rect.x > c_render_rect.x or
            c_page_rect.y > c_render_rect.y or
            c_page_rect.x + c_page_rect.w < c_render_rect.x + c_render_rect.w or
            c_page_rect.y + c_page_rect.h < c_render_rect.y + c_render_rect.h
        ):
            raise ValueError('render_rect must be inside page_rect')
        row_size = calculate_row_size(c_render_rect.w, row_alignment, pixel_format._bpp)
        result = allocate_image_memory(row_size, c_render_rect.h, buffer, &memory)
        if ddjvu_page_render(<ddjvu_page_t*> self.ddjvu_job, mode, &c_page_rect, &c_render_rect, pixel_format.ddjvu_format, row_size, <char*> memory) == 0:
            raise _NotAvailable_
        return result

    def __dealloc__(self):
        if self.ddjvu_job == NULL:
            return
        ddjvu_page_release(<ddjvu_page_t*> self.ddjvu_job)
        self.ddjvu_job = NULL

cdef PageJob PageJob_from_c(ddjvu_page_t* ddjvu_page):
    cdef PageJob job
    job = Job_from_c(<ddjvu_job_t*> ddjvu_page)
    return job

cdef class Job:

    '''
    A job.
    '''

    def __cinit__(self, **kwargs):
        check_sentinel(self, kwargs)
        self._context = None
        self.ddjvu_job = NULL
        self._condition = Condition()
        self._queue = Queue()

    cdef object __init(self, Context context, ddjvu_job_t *ddjvu_job):
        # Assumption: loft_lock is already acquired.
        assert context != None and ddjvu_job != NULL
        self._context = context
        self.ddjvu_job = ddjvu_job
        _job_loft.add(self)
        _job_weak_loft[voidp_to_int(ddjvu_job)] = self

    cdef object __clear(self):
        with nogil: acquire_lock(loft_lock, WAIT_LOCK)
        try:
            _job_loft.discard(self)
        finally:
            release_lock(loft_lock)

    property status:
        '''
        Return a JobException subclass indicating the job status.
        '''
        def __get__(self):
            return JobException_from_c(ddjvu_job_status(self.ddjvu_job))

    property is_error:
        '''
        Indicate whether the job failed.
        '''
        def __get__(self):
            return bool(ddjvu_job_error(self.ddjvu_job))

    property is_done:
        '''
        Indicate whether the decoding job is done.
        '''
        def __get__(self):
            return bool(ddjvu_job_done(self.ddjvu_job))

    def wait(self):
        '''
        J.wait() -> None

        Wait until the job is done.
        '''
        while 1:
            self._condition.acquire()
            try:
                if ddjvu_job_done(self.ddjvu_job):
                    break
                self._condition.wait()
            finally:
                self._condition.release()

    def stop(self):
        '''
        J.stop() -> None

        Attempt to cancel the job.

        This is a best effort method. There no guarantee that the job will
        actually stop.
        '''
        ddjvu_job_stop(self.ddjvu_job)

    property message_queue:
        '''
        Return the internal message queue.
        '''
        def __get__(self):
            return self._queue

    def get_message(self, wait=1):
        '''
        J.get_message(wait=True) -> a Message or None

        Get message from the internal job queue.
        Return None if wait is false and no message is available.
        '''
        try:
            return self._queue.get(wait)
        except Empty:
            return

    def __iter__(self):
        return self

    def __next__(self):
        return self.get_message()

    def __dealloc__(self):
        if self.ddjvu_job == NULL:
            return
        ddjvu_job_release(self.ddjvu_job)
        self.ddjvu_job = NULL

cdef Job Job_from_c(ddjvu_job_t* ddjvu_job):
    cdef Job result
    if ddjvu_job == NULL:
        result = None
    else:
        with nogil: acquire_lock(loft_lock, WAIT_LOCK)
        try:
            result = _job_weak_loft.get(voidp_to_int(ddjvu_job))
        finally:
            release_lock(loft_lock)
    return result

cdef class AffineTransform:

    '''
    AffineTransform((x0, y0, w0, h0), (x1, y1, w1, h1))
      -> an affine coordinate transformation

    The object represents an affine coordinate transformation that maps points
    from rectangle (x0, y0, w0, h0) to rectangle (x1, y1, w1, h1).
    '''

    def __cinit__(self, input, output):
        cdef ddjvu_rect_t c_input
        cdef ddjvu_rect_t c_output
        self.ddjvu_rectmapper = NULL
        (c_input.x, c_input.y, c_input.w, c_input.h) = input
        (c_output.x, c_output.y, c_output.w, c_output.h) = output
        self.ddjvu_rectmapper = ddjvu_rectmapper_create(&c_input, &c_output)

    def rotate(self, int n):
        '''
        A.rotate(n) -> None

        Rotate the output rectangle counter-clockwise by n degrees.
        '''
        if n % 90:
            raise ValueError('n must a multiple of 90')
        else:
            ddjvu_rectmapper_modify(self.ddjvu_rectmapper, n/90, 0, 0)

    def __call__(self, value):
        cdef ddjvu_rect_t rect
        IF PY3K:
            next = iter(value).__next__
        ELSE:
            next = iter(value).next
        try:
            rect.x = next()
            rect.y = next()
        except StopIteration:
            raise ValueError('value must be a pair or a 4-tuple')
        try:
            rect.w = next()
        except StopIteration:
            ddjvu_map_point(self.ddjvu_rectmapper, &rect.x, &rect.y)
            return (rect.x, rect.y)
        try:
            rect.h = next()
        except StopIteration:
            raise ValueError('value must be a pair or a 4-tuple')
        try:
            next()
        except StopIteration:
            pass
        else:
            raise ValueError('value must be a pair or a 4-tuple')
        ddjvu_map_rect(self.ddjvu_rectmapper, &rect)
        return (rect.x, rect.y, int(rect.w), int(rect.h))

    def apply(self, value):
        '''
        A.apply((x0, y0)) -> (x1, y1)
        A.apply((x0, y0, w0, h0)) -> (x1, y1, w1, h1)

        Apply the coordinate transform to a point or a rectangle.
        '''
        return self(value)

    def inverse(self, value):
        '''
        A.inverse((x0, y0)) -> (x1, y1)
        A.inverse((x0, y0, w0, h0)) -> (x1, y1, w1, h1)

        Apply the inverse coordinate transform to a point or a rectangle.
        '''
        cdef ddjvu_rect_t rect
        IF PY3K:
            next = iter(value).__next__
        ELSE:
            next = iter(value).next
        try:
            rect.x = next()
            rect.y = next()
        except StopIteration:
            raise ValueError('value must be a pair or a 4-tuple')
        try:
            rect.w = next()
        except StopIteration:
            ddjvu_unmap_point(self.ddjvu_rectmapper, &rect.x, &rect.y)
            return (rect.x, rect.y)
        try:
            rect.h = next()
        except StopIteration:
            raise ValueError('value must be a pair or a 4-tuple')
        try:
            next()
        except StopIteration:
            pass
        else:
            raise ValueError('value must be a pair or a 4-tuple')
        ddjvu_unmap_rect(self.ddjvu_rectmapper, &rect)
        return (rect.x, rect.y, int(rect.w), int(rect.h))

    def mirror_x(self):
        '''
        A.mirror_x()

        Reverse the X coordinates of the output rectangle.
        '''
        ddjvu_rectmapper_modify(self.ddjvu_rectmapper, 0, 1, 0)

    def mirror_y(self):
        '''
        A.mirror_y()

        Reverse the Y coordinates of the output rectangle.
        '''
        ddjvu_rectmapper_modify(self.ddjvu_rectmapper, 0, 0, 1)

    def __dealloc__(self):
        if self.ddjvu_rectmapper != NULL:
            ddjvu_rectmapper_release(self.ddjvu_rectmapper)

cdef class Message:
    '''
    An abstract message.
    '''

    def __cinit__(self, **kwargs):
        check_sentinel(self, kwargs)
        self.ddjvu_message = NULL

    cdef object __init(self):
        if self.ddjvu_message == NULL:
            raise SystemError
        self._context = Context_from_c(self.ddjvu_message.m_any.context)
        self._document = Document_from_c(self.ddjvu_message.m_any.document)
        self._page_job = PageJob_from_c(self.ddjvu_message.m_any.page)
        self._job = Job_from_c(self.ddjvu_message.m_any.job)

    property context:
        '''
        Return the concerned Context.
        '''
        def __get__(self):
            return self._context

    property document:
        '''
        Return the concerned Document or None.
        '''
        def __get__(self):
            return self._document

    property page_job:
        '''
        Return the concerned PageJob or None.
        '''
        def __get__(self):
            return self._page_job

    property job:
        '''
        Return the concerned Job or None.
        '''
        def __get__(self):
            return self._job

cdef class ErrorMessage(Message):
    '''
    An ErrorMessage is generated whenever the decoder or the DDJVU API
    encounters an error condition. All errors are reported as error messages
    because they can occur asynchronously.
    '''

    cdef object __init(self):
        Message.__init(self)
        IF HAVE_LANGINFO_H:
            locale_encoding = charp_to_string(nl_langinfo(CODESET))
        ELSE:
            # Presumably a Windows system.
            import locale
            locale_encoding = locale.getpreferredencoding()
        if self.ddjvu_message.m_error.message != NULL:
            # Things can go awry if user calls setlocale() between the time the
            # message was created and the time it was received. Let's hope it
            # never happens, but don't throw an exception if it did anyway.
            self._message = self.ddjvu_message.m_error.message.decode(locale_encoding, 'replace')
        else:
            self._message = None
        if self.ddjvu_message.m_error.function != NULL:
            # Should be ASCII-only, so don't care about encoding.
            function = charp_to_string(self.ddjvu_message.m_error.function)
        else:
            function = None
        if self.ddjvu_message.m_error.filename != NULL:
            # Should be ASCII-only, so don't care about encoding.
            filename = charp_to_string(self.ddjvu_message.m_error.filename)
        else:
            filename = None
        self._location = (function, filename, self.ddjvu_message.m_error.lineno)

    property message:
        '''
        Return the actual error message, as text.
        '''
        def __get__(self):
            return self._message

    property location:
        '''
        Return a (function, filename, line_no) tuple indicating where the
        error was detected.
        '''
        def __get__(self):
            return self._location

    IF PY3K:
        def __str__(self):
            return self.message
    ELSE:
        def __str__(self):
            IF HAVE_LANGINFO_H:
                locale_encoding = charp_to_string(nl_langinfo(CODESET))
            ELSE:
                # Presumably a Windows system.
                import locale
                locale_encoding = locale.getpreferredencoding()
            return self.message.encode(locale_encoding, 'replace')
        def __unicode__(self):
            return self.message

    def __repr__(self):
        return '<%s: %r at %r>' % (get_type_name(ErrorMessage), self.message, self.location)

cdef class InfoMessage(Message):
    '''
    A InfoMessage provides informational text indicating the progress of the
    decoding process. This might be displayed in the browser status bar.
    '''

    cdef object __init(self):
        Message.__init(self)
        self._message = charp_to_string(self.ddjvu_message.m_error.message)

    property message:
        '''
        Return the actual information message, as text.
        '''
        def __get__(self):
            return self._message

cdef class Stream:
    '''
    Data stream.

    Use new_stream_message.stream to obtain instances of this class.
    '''

    def __cinit__(self, Document document not None, int streamid, **kwargs):
        check_sentinel(self, kwargs)
        self._streamid = streamid
        self._document = document
        self._open = 1

    def close(self):
        '''
        S.close() -> None

        Indicate that no more data will be provided on the particular stream.
        '''
        ddjvu_stream_close(self._document.ddjvu_document, self._streamid, 0)
        self._open = 0

    def abort(self):
        '''
        S.abort() -> None

        Indicate that no more data will be provided on the particular stream,
        because the user has interrupted the data transfer (for instance by
        pressing the stop button of a browser) and that the decoding threads
        should be stopped as soon as feasible.
        '''
        ddjvu_stream_close(self._document.ddjvu_document, self._streamid, 1)
        self._open = 0

    def flush(self):
        '''
        S.flush() -> None

        Do nothing. (This method is provided solely to implement Python's
        file-like interface.)
        '''

    def read(self, size=None):
        '''
        S.read([size])

        Raise IOError. (This method is provided solely to implement Python's
        file-like interface.)
        '''
        raise IOError('write-only data stream')

    def write(self, data):
        '''
        S.write(data) -> None

        Provide raw data to the DjVu decoder.

        This method should be called as soon as the data is available, for
        instance when receiving DjVu data from a network connection.
        '''
        cdef char* raw_data
        cdef Py_ssize_t length
        if self._open:
            bytes_to_charp(data, &raw_data, &length)
            ddjvu_stream_write(self._document.ddjvu_document, self._streamid, raw_data, length)
        else:
            raise IOError('I/O operation on closed file')

    def __dealloc__(self):
        if <object>self._document is None:
            return
        if self._open:
            ddjvu_stream_close(self._document.ddjvu_document, self._streamid, 1)

cdef class NewStreamMessage(Message):

    '''
    A NewStreamMessage is generated whenever the decoder needs to access raw
    DjVu data. The caller must then provide the requested data using the
    .stream file-like object.

    In the case of indirect documents, a single decoder might simultaneously
    request several streams of data.

    '''

    cdef object __init(self):
        Message.__init(self)
        self._stream = Stream(self.document, self.ddjvu_message.m_newstream.streamid, sentinel = the_sentinel)
        self._name = charp_to_string(self.ddjvu_message.m_newstream.name)
        self._uri = charp_to_string(self.ddjvu_message.m_newstream.url)

    property stream:
        '''
        Return the concerned Stream.
        '''
        def __get__(self):
            return self._stream

    property name:
        '''
        The first NewStreamMessage message always has .name set to None.
        It indicates that the decoder needs to access the data in the main DjVu
        file.

        Further NewStreamMessage messages messages are generated to access the
        auxiliary files of indirect or indexed DjVu documents. .name then
        provides the base name of the auxiliary file.
        '''
        def __get__(self):
            return self._name

    property uri:
        '''
        Return the requrested URI.

        URI is is set according to the uri argument provided to function
        Context.new_document(). The first NewMessageStream message always
        contain the URI passed to Context.new_document(). Subsequent
        NewMessageStream messages contain the URI of the auxiliary files for
        indirect or indexed DjVu documents.
        '''
        def __get__(self):
            return self._uri

cdef class DocInfoMessage(Message):
    '''
    A DocInfoMessage indicates that basic information about the document has
    been obtained and decoded. Not much can be done before this happens.

    Check Document.decoding_status to determine whether the operation was
    successful.
    '''

cdef class PageInfoMessage(Message):
    '''
    The page decoding process generates a PageInfoMessage:

    - when basic page information is available and before any RelayoutMessage
      or RedisplayMessage,
    - when the page decoding thread terminates.

    You can distinguish both cases using PageJob.status.

    A PageInfoMessage may be also generated as a consequence of reading
    Page.get_info() or Page.dump.
    '''

cdef class ChunkMessage(Message):
    '''
    A ChunkMessage indicates that an additional chunk of DjVu data has been
    decoded.
    '''

cdef class RelayoutMessage(ChunkMessage):
    '''
    A RelayoutMessage is generated when a DjVu viewer should recompute the
    layout of the page viewer because the page size and resolution information
    has been updated.
    '''

cdef class RedisplayMessage(ChunkMessage):
    '''
    A RedisplayMessage is generated when a DjVu viewer should call
    PageJob.render() and redisplay the page. This happens, for instance, when
    newly decoded DjVu data provides a better image.
    '''

cdef class ThumbnailMessage(Message):
    '''
    A ThumbnailMessage is sent when additional thumbnails are available.
    '''

    cdef object __init(self):
        Message.__init(self)
        self._page_no = self.ddjvu_message.m_thumbnail.pagenum

    property thumbnail:
        '''
        Return the Thumbnail.

        Raise NotAvailable if the Document has been garbage-collected.
        '''
        def __get__(self):
            if self._document is None:
                raise _NotAvailable_
            return self._document.pages[self._page_no].thumbnail

cdef class ProgressMessage(Message):
    '''
    A ProgressMessage is generated to indicate progress towards the
    completion of a print or save job.
    '''

    cdef object __init(self):
        Message.__init(self)
        self._percent = self.ddjvu_message.m_progress.percent
        self._status = self.ddjvu_message.m_progress.status

    property percent:
        '''
        Return the percent of the job done.
        '''
        def __get__(self):
            return self._percent

    property status:
        '''
        Return a JobException subclass indicating the current job status.
        '''
        def __get__(self):
            return JobException_from_c(self._status)

cdef object MESSAGE_MAP
MESSAGE_MAP = \
{
    DDJVU_ERROR: ErrorMessage,
    DDJVU_INFO: InfoMessage,
    DDJVU_NEWSTREAM: NewStreamMessage,
    DDJVU_DOCINFO: DocInfoMessage,
    DDJVU_PAGEINFO: PageInfoMessage,
    DDJVU_RELAYOUT: RelayoutMessage,
    DDJVU_REDISPLAY: RedisplayMessage,
    DDJVU_CHUNK: ChunkMessage,
    DDJVU_THUMBNAIL: ThumbnailMessage,
    DDJVU_PROGRESS: ProgressMessage
}

cdef Message Message_from_c(ddjvu_message_t* ddjvu_message):
    cdef Message message
    if ddjvu_message == NULL:
        return
    try:
        klass = MESSAGE_MAP[ddjvu_message.m_any.tag]
    except KeyError:
        raise SystemError
    message = klass(sentinel = the_sentinel)
    message.ddjvu_message = ddjvu_message
    message.__init()
    return message

cdef object JOB_EXCEPTION_MAP
cdef object JOB_FAILED_SYMBOL, JOB_STOPPED_SYMBOL

JOB_FAILED_SYMBOL = Symbol('failed')
JOB_STOPPED_SYMBOL = Symbol('stopped')

cdef object JobException_from_sexpr(object sexpr):
    if typecheck(sexpr, SymbolExpression):
        if sexpr.value is JOB_FAILED_SYMBOL:
            raise JobFailed
        elif sexpr.valu is JOB_STOPPED_SYMBOL:
            raise JobStopped

cdef JobException_from_c(ddjvu_status_t code):
    try:
        return JOB_EXCEPTION_MAP[code]
    except KeyError:
        raise SystemError

class JobException(Exception):
    '''
    Status of a job. Possibly, but not necessarily, exceptional.
    '''

class JobNotDone(JobException):
    '''
    Operation is not yet done.
    '''

class JobNotStarted(JobNotDone):
    '''
    Operation was not even started.
    '''

class JobStarted(JobNotDone):
    '''
    Operation is in progress.
    '''

class JobDone(JobException):
    '''
    Operation finished.
    '''

class JobOK(JobDone):
    '''
    Operation finished successfully.
    '''

class JobFailed(JobDone):
    '''
    Operation failed because of an error.
    '''

class JobStopped(JobFailed):
    '''
    Operation was interrupted by user.
    '''

JOB_EXCEPTION_MAP = \
{
    DDJVU_JOB_NOTSTARTED: JobNotStarted,
    DDJVU_JOB_STARTED: JobStarted,
    DDJVU_JOB_OK: JobOK,
    DDJVU_JOB_FAILED: JobFailed,
    DDJVU_JOB_STOPPED: JobStopped
}

cdef class _SexprWrapper:

    def __cinit__(self, document, **kwargs):
        check_sentinel(self, kwargs)
        self._document_weakref = weakref.ref(document)

    def __call__(self):
        return cexpr2py(self._cexpr)

    def __dealloc__(self):
        cdef Document document
        if self._cexpr == NULL:
            return
        document = self._document_weakref()
        if document is None:
            return
        ddjvu_miniexp_release(document.ddjvu_document, self._cexpr)

cdef _SexprWrapper wrap_sexpr(Document document, cexpr_t cexpr):
    cdef _SexprWrapper result
    result = _SexprWrapper(document, sentinel = the_sentinel)
    result._cexpr = cexpr
    return result

cdef class DocumentOutline(DocumentExtension):
    '''
    DocumentOutline(document) -> a document outline
    '''

    def __cinit__(self, Document document not None):
        self._document = document
        self._sexpr = None

    cdef object _update_sexpr(self):
        if self._sexpr is not None:
            return
        self._sexpr = wrap_sexpr(
            self._document,
            ddjvu_document_get_outline(self._document.ddjvu_document)
        )

    def wait(self):
        '''
        O.wait() -> None

        Wait until the associated S-expression is available.
        '''
        while 1:
            self._document._condition.acquire()
            try:
                try:
                    self.sexpr
                    return
                except NotAvailable:
                    self._document._condition.wait()
            finally:
                self._document._condition.release()

    property sexpr:
        '''
        Return the associated S-expression. See "Outline/Bookmark syntax" in
        the djvused manual page.

        If the S-expression is not available, raise NotAvailable exception.
        Then, PageInfoMessage messages with empty page_job may be emitted.

        Possible exceptions: NotAvailable, JobFailed.
        '''
        def __get__(self):
            self._update_sexpr()
            try:
                sexpr = self._sexpr()
                exception = JobException_from_sexpr(sexpr)
                if exception is not None:
                    raise exception
                return sexpr
            except InvalidExpression:
                self._sexpr = None
                raise _NotAvailable_

    def __repr__(self):
        return '%s(%r)' % (get_type_name(DocumentOutline), self._document)

cdef class Annotations:
    '''
    Document or page annotation.

    Don't use this class directly, use one of its subclasses.
    '''

    def __cinit__(self, *args, **kwargs):
        if typecheck(self, DocumentAnnotations):
            return
        if typecheck(self, PageAnnotations):
            return
        raise_instantiation_error(type(self))

    cdef object _update_sexpr(self):
        raise NotImplementedError

    def wait(self):
        '''
        A.wait() -> None

        Wait until the associated S-expression is available.
        '''
        while 1:
            self._document._condition.acquire()
            try:
                try:
                    self.sexpr
                    return
                except NotAvailable:
                    self._document._condition.wait()
            finally:
                self._document._condition.release()

    property sexpr:
        '''
        Return the associated S-expression. See "Annotation syntax" in the
        djvused manual page.

        If the S-expression is not available, raise NotAvailable exception.
        Then, PageInfoMessage messages with empty page_job may be emitted.

        Possible exceptions: NotAvailable, JobFailed.
        '''
        def __get__(self):
            self._update_sexpr()
            try:
                sexpr = self._sexpr()
                exception = JobException_from_sexpr(sexpr)
                if exception is not None:
                    raise exception
                return sexpr
            except InvalidExpression:
                self._sexpr = None
                raise _NotAvailable_

    property background_color:
        '''
        Parse the annotations and extract the desired background color as
        a color string '(#FFFFFF)'. See '(background ...)' in the
        djvused manual page.

        Return None if this information is not specified.
        '''
        def __get__(self):
            cdef char* result
            result = ddjvu_anno_get_bgcolor(self._sexpr._cexpr)
            if result == NULL:
                return
            return result

    property zoom:
        '''
        Parse the annotations and extract the desired zoom factor. See
        '(zoom ...)' in the djvused manual page.

        Return None if this information is not specified.
        '''
        def __get__(self):
            cdef char* result
            result = ddjvu_anno_get_zoom(self._sexpr._cexpr)
            if result == NULL:
                return
            return result

    property mode:
        '''
        Parse the annotations and extract the desired display mode. See
        '(mode ...)' in the djvused manual page.

        Return zero if this information is not specified.
        '''
        def __get__(self):
            cdef char* result
            result = ddjvu_anno_get_mode(self._sexpr._cexpr)
            if result == NULL:
                return
            return result

    property horizontal_align:
        '''
        Parse the annotations and extract how the page image should be aligned
        horizontally. See '(align ...)' in the djvused manual page.

        Return None if this information is not specified.
        '''
        def __get__(self):
            cdef char* result
            result = ddjvu_anno_get_horizalign(self._sexpr._cexpr)
            if result == NULL:
                return
            return result

    property vertical_align:
        '''
        Parse the annotations and extract how the page image should be aligned
        vertically. See '(align ...)' in the djvused manual page.

        Return None if this information is not specified.
        '''
        def __get__(self):
            cdef char* result
            result = ddjvu_anno_get_vertalign(self._sexpr._cexpr)
            if result == NULL:
                return
            return result

    property hyperlinks:
        '''
        Return an associated Hyperlinks object.
        '''
        def __get__(self):
            return Hyperlinks(self)

    property metadata:
        '''
        Return an associated Metadata object.
        '''
        def __get__(self):
            return Metadata(self)

cdef class DocumentAnnotations(Annotations):
    '''
    DocumentAnnotations(document[, shared=True]) -> document-wide annotations

    If shared is true and no document-wide annotations are available, shared
    annotations are considered document-wide.

    See also "Document annotations and metadata" in the djvuchanges.txt file.

    '''

    def __cinit__(self, Document document not None, shared=1):
        self._document = document
        self._compat = shared
        self._sexpr = None

    cdef object _update_sexpr(self):
        if self._sexpr is not None:
            return
        self._sexpr = wrap_sexpr(
            self._document,
            ddjvu_document_get_anno(self._document.ddjvu_document, self._compat)
        )

    property document:
        '''
        Return the concerned Document.
        '''
        def __get__(self):
            return self._document

cdef class PageAnnotations(Annotations):

    '''
    PageAnnotation(page) -> page annotations
    '''

    def __cinit__(self, Page page not None):
        self._document = page._document
        self._page = page
        self._sexpr = None

    cdef object _update_sexpr(self):
        if self._sexpr is not None:
            return
        self._sexpr = wrap_sexpr(
            self._page._document,
            ddjvu_document_get_pageanno(self._page._document.ddjvu_document, self._page._n)
        )

    property page:
        '''
        Return the concerned page.
        '''
        def __get__(self):
            return self._page

TEXT_DETAILS_PAGE = Symbol('page')
TEXT_DETAILS_COLUMN = Symbol('column')
TEXT_DETAILS_REGION = Symbol('region')
TEXT_DETAILS_PARAGRAPH = Symbol('para')
TEXT_DETAILS_LINE = Symbol('line')
TEXT_DETAILS_WORD = Symbol('word')
TEXT_DETAILS_CHARACTER = Symbol('char')
TEXT_DETAILS_ALL = None

cdef object TEXT_DETAILS
TEXT_DETAILS = {
    TEXT_DETAILS_PAGE: 7,
    TEXT_DETAILS_COLUMN: 6,
    TEXT_DETAILS_REGION: 5,
    TEXT_DETAILS_PARAGRAPH: 4,
    TEXT_DETAILS_LINE: 3,
    TEXT_DETAILS_WORD: 2,
    TEXT_DETAILS_CHARACTER: 1,
}

def cmp_text_zone(zonetype1, zonetype2):
    '''
    cmp_text_zone(zonetype1, zonetype2) -> integer

    Return:

    - negative if zonetype1 is more concrete than zonetype2;
    - zero if zonetype1 == zonetype2;
    - positive if zonetype1 is more general than zonetype2.

    Possible zone types:

    - TEXT_ZONE_PAGE,
    - TEXT_ZONE_COLUMN,
    - TEXT_ZONE_REGION,
    - TEXT_ZONE_PARAGRAPH,
    - TEXT_ZONE_LINE,
    - TEXT_ZONE_WORD,
    - TEXT_ZONE_CHARACTER.
    '''
    if not typecheck(zonetype1, Symbol) or not typecheck(zonetype2, Symbol):
        raise TypeError('zonetype must be a symbol')
    try:
        n1 = TEXT_DETAILS[zonetype1]
        n2 = TEXT_DETAILS[zonetype2]
    except KeyError:
        raise ValueError('zonetype must be equal to TEXT_ZONE_PAGE, or TEXT_ZONE_COLUMN, or TEXT_ZONE_REGION, or TEXT_ZONE_PARAGRAPH, or TEXT_ZONE_LINE, or TEXT_ZONE_WORD, or TEXT_ZONE_CHARACTER')
    if n1 < n2:
        return -1
    elif n1 > n2:
        return 1
    else:
        return 0

cdef class PageText:
    '''
    PageText(page, details=TEXT_DETAILS_ALL) -> wrapper around page text

    details controls the level of details in the returned S-expression:

    - TEXT_DETAILS_PAGE,
    - TEXT_DETAILS_COLUMN,
    - TEXT_DETAILS_REGION,
    - TEXT_DETAILS_PARAGRAPH,
    - TEXT_DETAILS_LINE,
    - TEXT_DETAILS_WORD,
    - TEXT_DETAILS_CHARACTER,
    - TEXT_DETAILS_ALL.
    '''

    def __cinit__(self, Page page not None, details=TEXT_DETAILS_ALL):
        if details is None:
            self._details = charp_to_bytes('', 0)
        elif not typecheck(details, Symbol):
            raise TypeError('details must be a symbol or none')
        elif details not in TEXT_DETAILS:
            raise ValueError('details must be equal to TEXT_DETAILS_PAGE, or TEXT_DETAILS_COLUMN, or TEXT_DETAILS_REGION, or TEXT_DETAILS_PARAGRAPH, or TEXT_DETAILS_LINE, or TEXT_DETAILS_WORD, or TEXT_DETAILS_CHARACTER or TEXT_DETAILS_ALL')
        else:
            self._details = details.bytes
        self._page = page
        self._sexpr = None

    cdef object _update_sexpr(self):
        if self._sexpr is None:
            self._sexpr = wrap_sexpr(
                self._page._document,
                ddjvu_document_get_pagetext(self._page._document.ddjvu_document, self._page._n, self._details)
            )

    def wait(self):
        '''
        PT.wait() -> None

        Wait until the associated S-expression is available.
        '''
        while 1:
            self._page._document._condition.acquire()
            try:
                try:
                    self.sexpr
                    return
                except NotAvailable:
                    self._page._document._condition.wait()
            finally:
                self._page._document._condition.release()

    property page:
        '''
        Return the concerned page.
        '''
        def __get__(self):
            return self._page

    property sexpr:
        '''
        Return the associated S-expression. See "Hidden text syntax" in the
        djvused manual page.

        If the S-expression is not available, raise NotAvailable exception.
        Then, PageInfoMessage messages with empty page_job may be emitted.

        Possible exceptions: NotAvailable, JobFailed.
        '''
        def __get__(self):
            self._update_sexpr()
            try:
                sexpr = self._sexpr()
                exception = JobException_from_sexpr(sexpr)
                if exception is not None:
                    raise exception
                return sexpr
            except InvalidExpression:
                self._sexpr = None
                raise _NotAvailable_

cdef class Hyperlinks:
    '''
    Hyperlinks(annotations) -> sequence of hyperlinks

    Parse the annotations and return a sequence of '(maparea ...)'
    S-expressions.

    See also '(maparea ...)' in the djvused manual page.
    '''

    def __cinit__(self, Annotations annotations not None):
        cdef cexpr_t* all
        cdef cexpr_t* current
        all = ddjvu_anno_get_hyperlinks(annotations._sexpr._cexpr)
        if all == NULL:
            raise MemoryError
        try:
            current = all
            self._sexpr = []
            while current[0]:
                list_append(self._sexpr, wrap_sexpr(annotations._document, current[0]))
                current = current + 1
        finally:
            libc_free(all)

    def __len__(self):
        return len(self._sexpr)

    def __getitem__(self, Py_ssize_t n):
        return self._sexpr[n]()

cdef class Metadata:
    '''
    Metadata(annotations) -> mapping of metadata

    Parse the annotations and return a mapping of metadata.

    See also '(metadata ...)' in the djvused manual page.
    '''

    def __cinit__(self, Annotations annotations not None):
        cdef cexpr_t* all
        cdef cexpr_t* current
        self._annotations = annotations
        all = ddjvu_anno_get_metadata_keys(annotations._sexpr._cexpr)
        if all == NULL:
            raise MemoryError
        try:
            current = all
            keys = []
            while current[0]:
                list_append(keys, unicode(wrap_sexpr(annotations._document, current[0])().value))
                current = current + 1
            self._keys = frozenset(keys)
        finally:
            libc_free(all)

    def __len__(self):
        return len(self._keys)

    def __getitem__(self, key):
        cdef _WrappedCExpr cexpr_key
        cdef char *s
        cexpr_key = py2cexpr(Symbol(key))
        s = ddjvu_anno_get_metadata(self._annotations._sexpr._cexpr, cexpr_key.cexpr())
        if s == NULL:
            raise KeyError(key)
        return decode_utf8(s)

    def keys(self):
        '''
        M.keys() -> sequence of M's keys
        '''
        return self._keys

    IF not PY3K:
        def iterkeys(self):
            '''
            M.iterkeys() -> an iterator over the keys of M
            '''
            return iter(self)

    def __iter__(self):
        return iter(self._keys)

    def values(self):
        '''
        M.values() -> list of M's values
        '''
        return map(self.__getitem__, self._keys)

    IF not PY3K:
        def itervalues(self):
            '''
            M.itervalues() -> an iterator over values of M
            '''
            return imap(self.__getitem__, self._keys)

    def items(self):
        '''
        M.items() -> list of M's (key, value) pairs, as 2-tuples
        '''
        return zip(self._keys, imap(self.__getitem__, self._keys))

    IF not PY3K:
        def iteritems(self):
            '''
            M.iteritems() -> an iterator over the (key, value) items of M
            '''
            return izip(self._keys, imap(self.__getitem__, self._keys))

    IF not PY3K:
        def has_key(self, k):
            '''
            M.has_key(k) -> True if D has a key k, else False
            '''
            return k in self

    def __contains__(self, k):
        return k in self._keys

__author__ = 'Jakub Wilk <jwilk@jwilk.net>'
IF PY3K:
    __version__ = decode_utf8(PYTHON_DJVULIBRE_VERSION)
ELSE:
    __version__ = PYTHON_DJVULIBRE_VERSION
__version__ = '%s/%d' % (__version__, DDJVU_VERSION)

# vim:ts=4 sw=4 et ft=pyrex
