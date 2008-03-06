# Copyright (c) 2007, 2008 Jakub Wilk <ubanus@users.sf.net>

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

Warning
-------
API of this module is a subject to change. You have been warned.
'''

include 'common.pxi'

cdef object weakref
import weakref

cdef object thread
import thread

cdef object Queue, Empty
from Queue import Queue, Empty

cdef object imap
from itertools import imap

cdef object sys, devnull
import sys
from os import devnull

cdef object StringIO
from cStringIO import StringIO

cdef object Symbol
from djvu.sexpr import Symbol

cdef object the_sentinel
the_sentinel = object()

cdef object _context_loft, _document_loft, _document_weak_loft, _job_loft, _job_weak_loft, loft_lock
_context_loft = {}
_document_loft = set()
_document_weak_loft = weakref.WeakValueDictionary()
_job_loft = set()
_job_weak_loft = weakref.WeakValueDictionary()
loft_lock = thread.allocate_lock()

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

class NotAvailable(Exception):
	'''
	A resource not (yet) available.
	'''

class DjVuLibreBug(Exception):

	'''
	Spotted a DjVuLibre bug.
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
		Return the concerned `Document`.
		'''

		def __get__(self):
			return self._document
	
cdef class DocumentPages(DocumentExtension):

	'''
	Pages of a document.

	Use `document.pages` to obtain instances of this class.
	
	Page indexing is zero-based, i.e. `pages[0]` stands for the very first page.
	'''

	def __cinit__(self, Document document not None, **kwargs):
		check_sentinel(self, kwargs)
		self._document = document
	
	def __len__(self):
		return ddjvu_document_get_pagenum((<Document>self.document).ddjvu_document)

	def __getitem__(self, key):
		if is_int(key):
			if key < 0:
				raise ValueError
			return Page(self.document, key)
		else:
			raise TypeError

cdef class Page:

	'''
	Page of a document.
	
	Use `document.pages[N]` to obtain instances of this class.
	'''

	def __cinit__(self, Document document not None, int n):
		self._document = document
		self._n = n

	property document:
		'''
		Return the `Document` which includes the page.
		'''
		def __get__(self):
			return self._document
	
	property n:
		'''
		Return the page number.
		
		Page indexing is zero-based, i.e. `0` stands for the very first page.
		'''
		def __get__(self):
			return self._n
	
	property thumbnail:
		'''
		Return a `Thumbnail` for the page.
		'''
		def __get__(self):
			return Thumbnail(self)

	property info:
		# FIXME: fix concurrency issues
		'''
		Attempt to obtain information about the page without decoding the page.

		If the information is available, return a `PageInfo`.

		Otherwise, raise `NotAvailable` exception. Then start fetching the page
		data, which causes emission of `PageInfoMessage` messages with empty
		`page_job`.

		In case of an error, `JobFail` is raised.
		'''
		def __get__(self):
			cdef ddjvu_status_t status
			cdef PageInfo page_info
			page_info = PageInfo(self._document, sentinel = the_sentinel)
			status = ddjvu_document_get_pageinfo(self._document.ddjvu_document, self._n, &page_info.ddjvu_pageinfo)
			ex = JobException_from_c(status)
			if ex == JobOK:
				return page_info
			elif ex == JobStarted:
				raise NotAvailable
			else:
				raise ex

	property dump:
		'''
		Return a text describing the contents of the page using the same format
		as the ``djvudump`` command. 

		If the information is not available, raise `NotAvailable` exception.
		Then `PageInfoMessage` messages with empty `page_job` may be emitted.
		'''
		def __get__(self):
			cdef char* s
			s = ddjvu_document_get_pagedump(self._document.ddjvu_document, self._n)
			if s == NULL:
				raise NotAvailable
			try:
				return decode_utf8(s)
			finally:
				libc_free(s)

	def decode(self, wait = True):
		'''
		P.decode(wait=True) -> a `PageJob`.

		Initiate data transfer and decoding threads for the page.

		If `wait` is true, wait until the job is done.

		If the method is called before receiving the `DocInfoMessage`,
		`NotAvailable` exception may be raised.
		'''
		cdef PageJob job
		cdef ddjvu_job_t* ddjvu_job
		loft_lock.acquire()
		try:
			ddjvu_job = <ddjvu_job_t*> ddjvu_page_create_by_pageno(self._document.ddjvu_document, self._n)
			if ddjvu_job == NULL:
				raise NotAvailable
			job = PageJob(sentinel = the_sentinel)
			job.__init(self._document._context, ddjvu_job)
		finally:
			loft_lock.release()
		if wait:
			job.wait()
		return job
	
	property annotations:
		'''
		Return `PageAnnotations` for the page.
		'''
		def __get__(self):
			return PageAnnotations(self)
	
	property text:
		'''
		Return `PageText` for the page.
		'''
		def __get__(self):
			return PageText(self)

cdef class Thumbnail:

	'''
	Thumbnail for a page.
	
	Use `page.thumbnail` to obtain instances of this class.
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
		Determine whether the thumbnail is available. Return a `JobException`
		subclass indicating the current job status.
		'''
		def __get__(self):
			return JobException_from_c(ddjvu_thumbnail_status(self._page._document.ddjvu_document, self._page._n, 0))
	
	def calculate(self):
		'''
		T.calculate() -> a `JobException`.

		Determine whether the thumbnail is available. If it's not, initiate the
		thumbnail calculating job. Regardless of its success, the completion of
		the job is signalled by a subsequent `ThumbnailMessage`.

		Return a `JobException` subclass indicating the current job status.
		'''
		return JobException_from_c(ddjvu_thumbnail_status(self._page._document.ddjvu_document, self._page._n, 1))

	def render(self, size, PixelFormat pixel_format not None, unsigned long row_alignment = 0, dry_run = False):
		'''
		T.render((w0, h0), pixel_format, row_alignment=1, dry_run=False) -> ((w1, h1, row_size), data).

		Render the thumbnail:
		* not larger than `w0` x `h0` pixels;
		* using the `pixel_format` pixel format;
		* with each row starting at `row_alignment` bytes boundary.

		Raise `NotAvailable` when no thumbnail is available.
		Otherwise, return a `(w1, h1, row_size), data` tuple:
		* `w1` and `h1` are actual thumbnail dimensions in pixels
		  (`w1 <= w0` and `h1 <= h0`);
		* `row_size` is length of each image row, in bytes;
		* `data` is `None` if `dry_run` is true; otherwise is contains the
		  actual image data.
		'''
		cdef int w, h
		cdef char* buffer
		cdef size_t buffer_size
		(w, h) = size
		if w <= 0 or h <= 0:
			raise ValueError
		row_size = calculate_row_size(w, row_alignment, pixel_format._bpp)
		if dry_run:
			buffer = NULL
		else:
			buffer = allocate_image_buffer(row_size, h, &buffer_size)
		try:
			if ddjvu_thumbnail_render(self._page._document.ddjvu_document, self._page._n, &w, &h, pixel_format.ddjvu_format, row_size, buffer):
				if dry_run:
					pybuffer = None
				else:
					pybuffer = charp_to_string(buffer, buffer_size)
				return (w, h, row_size), pybuffer
			else:
				raise NotAvailable
		finally:
			py_free(buffer)

cdef class DocumentFiles(DocumentExtension):

	'''
	Component files of a document.

	Use `document.files` to obtain instances of this class.
	
	File indexing is zero-based, i.e. `files[0]` stands for the very first file.
	'''

	def __cinit__(self, Document document not None, **kwargs):
		check_sentinel(self, kwargs)
		self._document = document
	
	def __len__(self):
		return ddjvu_document_get_filenum((<Document>self.document).ddjvu_document)

	def __getitem__(self, key):
		return File(self.document, key, sentinel = the_sentinel)

cdef class File:

	'''
	Component file of a document.

	Use `document.files[N]` to obtain instances of this class.
	'''

	def __cinit__(self, Document document not None, int n, **kwargs):
		check_sentinel(self, kwargs)
		self._document = document
		self._n = n
	
	property document:
		'''Return the `Document` which includes the component file.'''
		def __get__(self):
			return self._document

	property n:
		'''
		Return the component file number.
		
		File indexing is zero-based, i.e. `0` stands for the very first file.
		'''
		def __get__(self):
			return self._n

	property info:
		'''
		Return information about the component file, i.e. a `FileInfo`.

		If the method is called before receiving the `DocInfoMessage`,
		`NotAvailable` exception may be raised.

		In case of an error, `JobFail` is raised.
		'''
		# FIXME: fix concurrency issues
		def __get__(self):
			cdef ddjvu_status_t status
			cdef FileInfo file_info
			file_info = FileInfo(self._document, sentinel = the_sentinel)
			status = ddjvu_document_get_fileinfo(self._document.ddjvu_document, self._n, &file_info.ddjvu_fileinfo)
			ex = JobException_from_c(status)
			if ex == JobOK:
				return file_info
			elif ex == JobStarted:
				raise NotAvailable
			else:
				raise ex

	property dump:
		'''
		Return a text describing the contents of the file using the same format
		as the ``djvudump`` command. 

		If the information is not available, raise `NotAvailable` exception.
		Then, `PageInfoMessage` messages with empty `page_job` may be emitted.
		'''
		def __get__(self):
			cdef char* s
			s = ddjvu_document_get_filedump(self._document.ddjvu_document, self._n)
			if s == NULL:
				raise NotAvailable
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
			raise TypeError
		if pages[i] < 0:
			raise ValueError
		pages[i] = pages[i] + 1
	return '--pages=' + (','.join(imap(str, pages)))

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

cdef class SaveJob(Job):

	'''
	Document saving job.

	Use `document.save(...)` to obtain instances of this class.
	'''

	def __cinit__(self, **kwargs):
		self._file = None

cdef class DocumentDecodingJob(Job):

	'''
	Document decoding job.

	Use `document.decoding_job` to obtain instances of this class.
	'''

	cdef object __init_ddj(self, Document document):
		self._context = document._context
		self._document = document
		self.ddjvu_job = <ddjvu_job_t*> document.ddjvu_document

	def __dealloc__(self):
		self.ddjvu_job = NULL # Don't allow `Job.__dealloc__` to release the job. 
	
	def __repr__(self):
		return '<%s for %r>' % (get_type_name(DocumentDecodingJob), self._document)

cdef class Document:

	'''
	DjVu document.

	Use `context.new_document(...)` to obtain instances of this class.
	'''

	def __cinit__(self, **kwargs):
		self.ddjvu_document = NULL
		if kwargs.get('sentinel') is not the_sentinel:
			raise_instantiation_error(type(self))
		self._pages = DocumentPages(self, sentinel = the_sentinel)
		self._files = DocumentFiles(self, sentinel = the_sentinel)
		self._context = None
		self._queue = Queue()
	
	cdef object __init(self, Context context, ddjvu_document_t *ddjvu_document):
		# Assumption: `loft_lock` is already acquired. 
		assert context != None and ddjvu_document != NULL
		self.ddjvu_document = ddjvu_document
		self._context = context
		_document_loft.add(self)
		_document_weak_loft[<long> ddjvu_document] = self

	cdef object __clear(self):
		loft_lock.acquire()
		try:
			_document_loft.discard(self)
		finally:
			loft_lock.release()

	property decoding_status:
		'''
		Return a `JobException` subclass indicating the decoding job status.
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
		Return the `DocumentDecodingJob`.
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
		* `DOCUMENT_TYPE_UNKNOWN`;
		* `DOCUMENT_TYPE_SINGLE_PAGE`: single-page document;
		* `DOCUMENT_TYPE_BUNDLED`: bundled mutli-page document;
		* `DOCUMENT_TYPE_INDIRECT`: indirect multi-page document;
		* (obsolete) `DOCUMENT_TYPE_OLD_BUNDLED`,
		* (obsolete) `DOCUMENT_TYPE_OLD_INDEXED`.

		Before receiving the `DocInfoMessage`, `DOCUMENT_TYPE_UNKNOWN` may be returned.
		'''
		def __get__(self):
			return ddjvu_document_get_type(self.ddjvu_document)

	property pages:
		'''
		Return the `DocumentPages`.
		'''
		def __get__(self):
			return self._pages
	
	property files:
		'''
		Return the `DocumentPages`.
		'''
		def __get__(self):
			return self._files
	
	property outline:
		'''
		Return the `DocumentOutline`.
		'''
		def __get__(self):
			return DocumentOutline(self)
	
	property annotations:
		'''
		Return the `DocumentAnnotations`.
		'''	
		def __get__(self):
			return DocumentAnnotations(self)

	def __dealloc__(self):
		if self.ddjvu_document == NULL:
			return
		ddjvu_document_release(self.ddjvu_document)
	
	def save(self, file = None, indirect = None, pages = None, wait = True):
		'''
		D.save(file=None, indirect=None, pages=<all-pages>, wait=True) -> a `SaveJob`.

		Saves the document as:
		* a bundled DjVu `file` or;
		* an indirect DjVu document with index file name `indirect`.

		`pages` argument specifies a subset of saved pages.

		If `wait` is true, wait until the job is done.

		**Warning**
		-----------
		Due to a DjVuLibre (<= 3.5.20) bug, this method may be broken.
		See http://bugs.debian.org/467282 for details.
		'''
		cdef char * optv[2]
		cdef int optc
		cdef SaveJob job
		optc = 0
		cdef FILE* output
		cdef Py_ssize_t i
		if indirect is None:
			if not is_file(file):
				raise TypeError
			output = file_to_cfile(file)
		else:
			if file is not None:
				raise TypeError
			if not is_string(indirect):
				raise TypeError
			# XXX ddjvu API documentation says that output should by NULL,
			# but we'd like to spot the DjVuLibre bug
			open(indirect, 'wb').close()
			file = open(devnull, 'wb')
			output = file_to_cfile(file)
			s1 = '--indirect=' + indirect
			optv[optc] = s1
			optc = optc + 1
		if pages is not None:
			s2 = pages_to_opt(pages, 1)
			optv[optc] = s2
			optc = optc + 1
		loft_lock.acquire()
		try:
			job = SaveJob(sentinel = the_sentinel)
			job.__init(self._context, ddjvu_document_save(self.ddjvu_document, output, optc, optv))
			job._file = file
		finally:
			loft_lock.release()
		if wait:
			job.wait()
			if indirect is not None:
				file = open(indirect, 'rb')
				file.seek(0, 2)
			if file.tell() == 0:
				raise DjVuLibreBug(467282)
		return job
	
	def export_ps(self, file, pages = None, eps = False, level = None, orientation = PRINT_ORIENTATION_AUTO, mode = DDJVU_RENDER_COLOR, zoom = None, color = True, srgb = True, gamma = None, copies = 1, frame = False, cropmarks = False, text = False, booklet = PRINT_BOOKLET_NO, booklet_max = 0, booklet_align = 0, booklet_fold = (18, 200), wait = True):
		'''
		D.export_ps(file, pages=<all-pages>, ..., wait=True) -> a `Job`.

		Convert the document into PostScript.

		`pages` argument specifies a subset of saved pages.

		If `wait` is true, wait until the job is done.

		Additional options
		------------------

		`eps`
			Produce an _Encapsulated_ PostScript file. Encapsulated PostScript
			files are suitable for embedding images into other documents.
			Encapsulated PostScript file can only contain a single page.
			Setting this option overrides the options `copies`, `orientation`,
			`zoom`, `cropmarks`, and `booklet`.
		`level`
			Selects the language level of the generated PostScript. Valid
			language levels are 1, 2, and 3. Level 3 produces the most compact
			and fast printing PostScript files. Some of these files however
			require a very modern printer. Level 2 is the default value. The
			generated PostScript files are almost as compact and work with all
			but the oldest PostScript printers. Level 1 can be used as a last
			resort option.
		`orientation`
			Specifies the pages orientation:
			`PRINT_ORIENTATION_AUTO`
				automatic
			`PRINT_ORIENTATION_PORTRAIT`
				portrait
			`PRINT_ORIENTATION_LANDSCAPE`
				landscape
		`mode`
			Specifies how pages should be decoded:
			`RENDER_COLOR`
				render all the layers of the DjVu documents
			`RENDER_BLACK`
				render only the foreground layer mask
			`RENDER_FOREGROUND`
				render only the foreground layer
			`RENDER_BACKGROUND`
				redner only the background layer
		`zoom`
			Specifies a zoom factor. The default zoom factor scales the image to
			fit the page.
		`color`
			Specifies whether to generate a color or a gray scale PostScript
			file. A gray scale PostScript files are smaller and marginally more
			portable.
		`srgb`
			The default value, True, generates a PostScript file using device
			independent colors in compliance with the sRGB specification.
			Modern printers then produce colors that match the original as well
			as possible. Specifying a false value generates a PostScript file
			using device dependent colors. This is sometimes useful with older
			printers. You can then use the `gamma` option to tune the output
			colors.
		`gamma`
			Specifies a gamma correction factor for the device dependent
			PostScript colors. Argument must be in range 0.3 to 5.0. Gamma
			correction normally pertains to cathodic screens only. It gets
			meaningful for printers because several models interpret device
			dependent RGB colors by emulating the color response of a cathodic
			tube.
		`copies`
			Specifies the number of copies to print.
		`frame`, 
			If true, generate a thin gray border representing the boundaries of
			the document pages.
		`cropmarks`
			If true, generate crop marks indicating where pages should be cut. 
		`text`
			Generate hidden text. See the warning below.
		`booklet`
			* PRINT_BOOKLET_NO
				Disable booklet mode. This is the default.
			* PRINT_BOOKLET_YES:
				Enable recto/verse booklet mode.
			* PRINT_BOOKLET_RECTO
				Enable recto booklet mode.
			* PRINT_BOOKLET_VERSO
				Enable verso booklet mode.
		`booklet_max`
			Specifies the maximal number of pages per booklet. A single printout
			might then be composed of several booklets. The argument is rounded
			up to the next multiple of 4. Specifying 0 sets no maximal number
			of pages and ensures that the printout will produce
			a single booklet. This is the default.
		`booklet_align`
			Specifies a positive or negative offset applied  o the verso of
			each sheet. The argument is expressed in points[1]_. This is useful
			with certain printers to ensure that both recto and verso are
			properly aligned. The default value is 0.
		`booklet_fold` (= `(base, increment)`)
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
		options = []
		if not is_file(file):
			raise TypeError
		output = file_to_cfile(file)
		if pages is not None:
			options.append(pages_to_opt(pages, 0))
		if eps:
			options.append('--format=eps')
		if level is not None:
			if not is_int(level):
				raise TypeError
			options.append('--level=%d' % level)
		if orientation is not None:
			if not is_string(booklet):
				raise TypeError
			options.append('--orientation=' + orientation)
		if not is_int(mode):
			raise TypeError
		try:
			mode = PRINT_RENDER_MODE_MAP[mode]
			if mode is not None:
				options.append('--mode=' + mode)
		except KeyError:
			raise ValueError
		if zoom is not None:
			if not is_int(zoom):
				raise TypeError
			options.append('--zoom=%d' % zoom)
		if not color:
			options.append('--color=no')
		if not srgb:
			options.append('--srgb=no')
		if gamma is not None:
			if not is_int(gamma) and not is_float(gamma):
				raise TypeError
			options.append('--gamma=%.16f' % gamma)
		if not is_int(copies):
			raise TypeError
		if copies != 1:
			options.append('--options=%d' % copies)
		if frame:
			options.append('--frame')
		if cropmarks:
			options.append('--cropmarks')
		if text:
			options.append('--text')
		if booklet is not None:
			if not is_string(booklet):
				raise TypeError
			options.append('--booklet=' + booklet)
		if not is_int(booklet_max):
			raise TypeError
		if booklet_max:
			options.append('--bookletmax=%d' % booklet_max)
		if not is_int(booklet_align):
			raise TypeError
		if booklet_align:
			options.append('--bookletalign=%d' % booklet_align)
		if is_int(booklet_fold):
			options.append('--bookletfold=%d' % booklet_fold)
		else:
			fold_base, fold_incr = booklet_fold
			if not is_int(fold_base) or not is_int(fold_incr):
				options.append('--bookletfold=%d+%d' % (fold_base, fold_incr))
		cdef char **optv
		cdef int optc
		optc = 0
		optv = <char**> py_malloc(len(options) * sizeof (char*))
		if optv == NULL:
			raise MemoryError
		try:
			for option in options:
				optv[optc] = option
				optc = optc + 1
			loft_lock.acquire()
			try:
				job = SaveJob(sentinel = the_sentinel)
				job.__init(self._context, ddjvu_document_print(self.ddjvu_document, output, optc, optv))
				job._file = file
			finally:
				loft_lock.release()
		finally:
			py_free(optv)
		if wait:
			job.wait()
		return job

	def get_message(self, wait = True):
		'''
		D.get_message(wait=True) -> a `Message` or `None`.

		Get message from the internal document queue.
		Return `None` if `wait` is false and no message is available.
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
		loft_lock.acquire()
		try:
			result = _document_weak_loft.get(<long> ddjvu_document)
		finally:
			loft_lock.release()
	return result

cdef class PageInfo:

	'''
	Rudimentary page information.

	Use `page.info` to obtain instances of this class.
	'''

	def __cinit__(self, Document document not None, **kwargs):
		if kwargs.get('sentinel') is not the_sentinel:
			raise_instantiation_error(type(self))
		self._document = document
	
	property document:
		'''
		Return the `Document` which includes the page.
		'''
		def __get__(self):
			return self._document
	
	property width:
		'''
		Return the page width, in pixels.
		'''
		def __get__(self):
			return self.ddjvu_pageinfo.width
	
	property height:
		'''
		Return the page height, in pixels.
		'''
		def __get__(self):
			return self.ddjvu_pageinfo.height
	
	property dpi:
		'''
		Return the page resolution, in dpi (dots per inch).
		'''
		def __get__(self):
			return self.ddjvu_pageinfo.dpi
	
	property rotation:
		'''
		Return the initial page rotation, in degrees.
		'''
		def __get__(self):
			return self.ddjvu_pageinfo.rotation * 90

	property version:
		'''
		Return the page version.
		'''
		def __get__(self):
			return self.ddjvu_pageinfo.version

cdef class FileInfo:

	'''
	Rudimentary compound file information.
	'''

	def __cinit__(self, Document document not None, **kwargs):
		if kwargs.get('sentinel') is not the_sentinel:
			raise_instantiation_error(type(self))
		self._document = document
	
	property document:
		'''
		Return the `Document` which includes the compound file.
		'''
		def __get__(self):
			return self._document
	
	property type:
		'''
		Return the type of the compound file:
		* `FILE_TYPE_PAGE`,
		* `FILE_TYPE_THUMBNAILS`,
		* `FILE_TYPE_INCLUDE`.
		'''
		def __get__(self):
			return charp_to_string(&self.ddjvu_fileinfo.type, 1)
	
	property n_page:
		'''
		Return the page number, or None when not applicable.

		Page indexing is zero-based, i.e. `0` stands for the very first page.
		'''	
		def __get__(self):
			if self.ddjvu_fileinfo.pageno < 0:
				return
			else:
				return self.ddjvu_fileinfo.pageno
	
	property size:
		'''
		Return the compound file size, or None when unknown.
		'''
		def __get__(self):
			if self.ddjvu_fileinfo.size < 0:
				return
			else:
				return self.ddjvu_fileinfo.size
	
	property id:
		'''
		Return the compound file identifier, or None.
		'''
		def __get__(self):
			cdef char* result
			result = <char*> self.ddjvu_fileinfo.id
			if result == NULL:
				return
			else:
				return decode_utf8(result)

	property name:
		'''
		Return the compound file name, or None.
		'''
		def __get__(self):
			cdef char* result
			result = <char*> self.ddjvu_fileinfo.name
			if result == NULL:
				return
			else:
				return decode_utf8(result)

	property title:
		'''
		Return the compound file title, or None.
		'''
		def __get__(self):
			cdef char* result
			result = <char*> self.ddjvu_fileinfo.title
			if result == NULL:
				return
			else:
				return decode_utf8(result)

class FileURI(str):
	'''
	See the `Document.new_document()` method.
	'''

cdef object Context_message_distributor
def _Context_message_distributor(Context self not None, sentinel):
	cdef Message message
	cdef Document document
	cdef Job job
	cdef PageJob page_job
	cdef ddjvu_message_t* ddjvu_message

	if sentinel is not the_sentinel:
		raise RuntimeError
	while True:
		with nogil:
			ddjvu_message = ddjvu_message_wait(self.ddjvu_context)
		try:
			try:
				message = Message_from_c(ddjvu_message)
			finally:
				ddjvu_message_pop(self.ddjvu_context)
			if message is None:
				raise SystemError
			# XXX Order of branches below is *crucial*. Do not change.
			if message._job is not None:
				job = message._job
				job._queue.put(message)
				if job.is_done:
					job.__clear()
			elif message._page_job is not None:
				raise SystemError # should not happen
			elif message._document is not None:
				document = message._document
				document._queue.put(message)
				if document.decoding_done:
					document.__clear()
			else:
				self._queue.put(message)
		except KeyboardInterrupt:
			raise
		except SystemExit:
			raise
		except Exception, ex:
			write_unraisable_exception(ex)
Context_message_distributor = _Context_message_distributor
del _Context_message_distributor

cdef class Context:

	def __cinit__(self, argv0 = None):
		if argv0 is None:
			argv0 = sys.argv[0]
		loft_lock.acquire()
		try:
			self.ddjvu_context = ddjvu_context_create(argv0)
			if self.ddjvu_context == NULL:
				raise MemoryError
			_context_loft[<long> self.ddjvu_context] = self
		finally:
			loft_lock.release()
		self._queue = Queue()
		thread.start_new_thread(Context_message_distributor, (self, the_sentinel))
	
	property cache_size:

		def __set__(self, value):
			value = int(value)
			if 0 < value < (1L << (8 * sizeof(unsigned long))):
				ddjvu_cache_set_size(self.ddjvu_context, value)
			else:
				raise ValueError('0 < cache_size < 2 * (sys.maxint + 1) is not satisfied')

		def __get__(self):
			return ddjvu_cache_get_size(self.ddjvu_context)

	def handle_message(self, message):
		'''
		C.handle_message(message).

		Synchronous versions (`wait=True`) of some methods calls this method for
		each received message, unless it's related to a job or a document.
		
		By default, does nothing. You may want to override this method to
		change this behaviour.
		'''
	
	def handle_job_message(self, message):
		'''
		C.handle_job_message(message).

		Synchronous versions (`wait=True`) of some methods calls this method for
		each received message related to a job.

		By default, does nothing. You may want to override this method to
		change this behaviour.
		'''
	
	def handle_document_message(self, message):
		'''
		C.handle_document_message(message).

		Synchronous versions (`wait=True`) of some methods calls this method for
		each received message related to a document.

		By default, does nothing. You may want to override this method to
		change this behaviour.
		'''

	def get_message(self, wait = True):
		'''
		C.get_message(wait=True) -> a `Message` or `None`.

		Get message from the internal context queue.
		Return `None` if `wait` is false and no message is available.
		'''
		try:
			return self._queue.get(wait)
		except Empty:
			return

	def new_document(self, uri, cache = True):
		'''
		C.new_document(uri, cache=True).

		Creates a decoder for a DjVu document and starts decoding. This
		method returns immediately. The decoding job then generates messages to
		request the raw data and to indicate the state of the decoding process.
		
		`uri` specifies an optional URI for the document. The URI follows the
		usual syntax (``protocol://machine/path``). It should not end with 
		a slash. It only serves two purposes:
		- The URI is used as a key for the cache of decoded pages.
		- The URI is used to document `NewStreamMessage` messages.
		
		Setting argument `cache` to a true vaule indicates that decoded pages
		should be cached when possible.
		
		It is important to understand that the URI is not used to access the
		data. The document generates `NewStreamMessage` messages to indicate
		which data is needed. The caller must then provide the raw data using 
		a `NewStereamMessage.stream` object.

		To open a local file, provide a `FileURI` instance as an `uri`.
		
		Localized characters in `uri` should be in URI-encoded.
		'''
		cdef Document document
		cdef ddjvu_document_t* ddjvu_document
		loft_lock.acquire()
		try:
			if typecheck(uri, FileURI):
				ddjvu_document = ddjvu_document_create_by_filename(self.ddjvu_context, uri, cache)
			else:
				ddjvu_document = ddjvu_document_create(self.ddjvu_context, uri, cache)
			if ddjvu_document == NULL:
				return
			document = Document(sentinel = the_sentinel)
			document.__init(self, ddjvu_document)
		finally:
			loft_lock.release()
		return document

	def __iter__(self):
		return self

	def __next__(self):
		return self.get_message()

	def clear_cache(self):
		'''
		C.clear_cache().
		'''
		ddjvu_cache_clear(self.ddjvu_context)

	def __dealloc__(self):
		ddjvu_context_release(self.ddjvu_context)

cdef Context Context_from_c(ddjvu_context_t* ddjvu_context):
	cdef Context result
	if ddjvu_context == NULL:
		result = None
	else:
		loft_lock.acquire()
		try:
			try:
				result = _context_loft[<long> ddjvu_context]
			except KeyError:
				raise SystemError
		finally:
			loft_lock.release()
	return result

RENDER_COLOR = DDJVU_RENDER_COLOR
RENDER_BLACK = DDJVU_RENDER_BLACK
RENDER_COLOR_ONLY = DDJVU_RENDER_COLORONLY
RENDER_MASK_ONLY = DDJVU_RENDER_MASKONLY
RENDER_BACKGROUND = DDJVU_RENDER_BACKGROUND
RENDER_FOREGROUND = DDJVU_RENDER_FOREGROUND

PAGE_TYPE_UNKNOWN = DDJVU_PAGETYPE_UNKNOWN
PAGE_TYPE_BITONAL =	DDJVU_PAGETYPE_BITONAL
PAGE_TYPE_PHOTO = DDJVU_PAGETYPE_PHOTO
PAGE_TYPE_COMPOUND = DDJVU_PAGETYPE_COMPOUND

cdef class PixelFormat:

	'''
	Abstract pixel format.

	Don't use this class directly, use one of its subclass.
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
			if (value > 0 and value < 64):
				ddjvu_format_set_ditherbits(self.ddjvu_format, value)
				self._dither_bpp = value
			else:
				raise ValueError
	
	property gamma:
		'''
		Gamma of the display for which the pixels are intended. This will be
		combined with the gamma stored in DjVu documents in order to compute 
		a suitable color correction.
		
		The default value is ``2.2``.
		'''
		def __get__(self):
			return self._gamma

		def __set__(self, double value):
			if (value >= 0.5 and value <= 5.0):
				ddjvu_format_set_gamma(self.ddjvu_format, value)
			else:
				raise ValueError
	
	def __dealloc__(self):
		if self.ddjvu_format != NULL:
			ddjvu_format_release(self.ddjvu_format)

	def __repr__(self):
		return '%s.%s()' % (self.__class__.__module__, self.__class__.__name__)

cdef class PixelFormatRgb(PixelFormat):

	'''
	PixelFormatRgb(byteorder='RGB') -> a pixel format.

	24-bit pixel format, with:
	- RGB (`byteorder='RGB'`) or
	- BGR (`byteorder='BGR'`)
	byte order.
	'''

	def __cinit__(self, char *byte_order = 'RGB', unsigned int bpp = 24):
		cdef unsigned int _format
		if strcmp(byte_order, 'RGB') == 0:
			self._rgb = 1
			_format = DDJVU_FORMAT_RGB24
		elif strcmp(byte_order, 'BGR') == 0:
			self._rgb = 0
			_format = DDJVU_FORMAT_BGR24
		else:
			raise ValueError
		if bpp != 24:
			raise ValueError
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
		return '%s.%s(byte_order = %r, bpp = %d)' % \
		(
			self.__class__.__module__, self.__class__.__name__,
			self.byte_order,
			self.bpp
		)
	
cdef class PixelFormatRgbMask(PixelFormat):

	'''
	PixelFormatRgbMask(red_mask, green_mask, blue_mask[, xor_value]) -> a pixel format.

	XXX
	'''

	def __cinit__(self, unsigned int red_mask, unsigned int green_mask, unsigned int blue_mask, unsigned int xor_value = 0, unsigned int bpp = 16):
		cdef unsigned int _format
		if bpp == 16:
			_format = DDJVU_FORMAT_RGBMASK16
		elif bpp == 32:
			_format = DDJVU_FORMAT_RGBMASK32
		else:
			raise ValueError
		self._bpp = self._dither_bpp = bpp
		(self._params[0], self._params[1], self._params[2], self._params[3]) = (red_mask, green_mask, blue_mask, xor_value)
		self.ddjvu_format = ddjvu_format_create(_format, 4, self._params)
	
	def __repr__(self):
		return '%s.%s(red_mask = 0x%0*x, green_mask = 0x%0*x, blue_mask = 0x%0*x, xor_value = 0x%0*x, bpp = %d)' % \
		(
			self.__class__.__module__, self.__class__.__name__,
			self.bpp/4, self._params[0],
			self.bpp/4, self._params[1],
			self.bpp/4, self._params[2],
			self.bpp/4, self._params[3],
			self.bpp,
		)
	
cdef class PixelFormatGrey(PixelFormat):

	'''
	PixelFormatGrey() -> a pixel format.
	
	8-bit, grey pixel format.
	'''

	def __cinit__(self, unsigned int bpp = 8):
		cdef unsigned int params[4]
		if bpp != 8:
			raise ValueError
		self._bpp = self._dither_bpp = bpp
		self.ddjvu_format = ddjvu_format_create(DDJVU_FORMAT_GREY8, 0, NULL)

	def __repr__(self):
		return '%s.%s(bpp = %d)' % (self.__class__.__module__, self.__class__.__name__, self.bpp)

cdef class PixelFormatPalette(PixelFormat):

	'''
	PixelFormatPalette(palette) -> a pixel format.

	Palette pixel format.

	XXX
	'''

	def __cinit__(self, palette, unsigned int bpp = 8):
		cdef int i
		palette_next = iter(palette).next
		for i from 0 <= i < 216:
			try:
				self._palette[i] = palette_next()
			except StopIteration:
				raise ValueError
		try:
			palette_next()
		except StopIteration:
			pass
		else:
			raise ValueError
		if bpp != 8:
			raise ValueError
		self._bpp = self._dither_bpp = bpp
		self.ddjvu_format = ddjvu_format_create(DDJVU_FORMAT_PALETTE8, 216, self._palette)

	def __repr__(self):
		cdef int i
		io = StringIO()
		io.write('%s.%s([' % (self.__class__.__module__, self.__class__.__name__))
		for i from 0 <= i < 215:
			io.write('0x%02x, ' % self._palette[i])
		io.write('0x%02x], bpp = %d)' % (self._palette[215], self.bpp))
		return io.getvalue()

cdef class PixelFormatPackedBits(PixelFormat):

	'''
	PixelFormatPackedBits(endianess) -> a pixel format.

	Bitonal, 1bpp pixel format with:
	- most significant bits on the left (`endianess='>'`) or
	- least significant bits on the left (`endianess='<'`).
	'''

	def __cinit__(self, char *endianess):
		cdef int _format
		if strcmp(endianess, '<') == 0:
			self._little_endian = 1
			_format = DDJVU_FORMAT_LSBTOMSB
		elif strcmp(endianess, '>') == 0:
			self._little_endian = 0
			_format = DDJVU_FORMAT_MSBTOLSB
		else:
			raise ValueError
		self._bpp = 1
		self._dither_bpp = 1
		self.ddjvu_format = ddjvu_format_create(_format, 0, NULL)
	
	property endianness:
		'''
		The endianess:
		- '<' (most significant bits on the left) or
		- '>' (least significant bits on the left).
		'''
		def __get__(self):
			if self._little_endian:
				return '<'
			else:
				return '>'
	
	def __repr__(self):
		return '%s.%s(%r)' % \
		(
			self.__class__.__module__, self.__class__.__name__,
			self.endianness
		)

cdef unsigned long calculate_row_size(unsigned long width, unsigned long row_alignment, int bpp):
	if bpp == 1:
		row_size = (width + 7) >> 3
	elif bpp & 7 == 0:
		row_size = width * (bpp >> 3)
	else:
		raise SystemError
	if row_alignment == 0:
		row_alignment = 1
	return ((row_size + (row_alignment - 1)) / row_alignment) * row_alignment

cdef char* allocate_image_buffer(unsigned long width, unsigned long height, size_t* buffer_size) except NULL:
	cdef char *buffer
	py_buffer_size = int(width) * int(height)
	try:
		buffer_size[0] = py_buffer_size
	except OverflowError:
		buffer = NULL
	else:
		buffer = <char*> py_malloc(buffer_size[0])
	if buffer == NULL:
		raise MemoryError('Unable to alocate %d bytes for an image buffer' % py_buffer_size)
	return buffer

cdef class PageJob(Job):

	'''
	A page decoding job.

	Use `page.decode(...)` to obtain instances of this class.
	'''

	cdef object __init(self, Context context, ddjvu_job_t *ddjvu_job):
		Job.__init(self, context, ddjvu_job)
	
	property width:
		'''
		Return the page width in pixels.

		Before receiving a `PageInfoMessage`, raise `NotAvailable`.
		'''
		def __get__(self):
			cdef int width
			width = ddjvu_page_get_width(<ddjvu_page_t*> self.ddjvu_job)
			if width == 0:
				raise NotAvailable
			else:
				return width
	
	property height:
		'''
		Return the page height in pixels.

		Before receiving a `PageInfoMessage`, raise `NotAvailable`.
		'''
		def __get__(self):
			cdef int height
			height = ddjvu_page_get_height(<ddjvu_page_t*> self.ddjvu_job)
			if height == 0:
				raise NotAvailable
			else:
				return height

	property resolution:
		'''
		Return the page resolution in pixels per inch (dpi).

		Before receiving a `PageInfoMessage`, raise `NotAvailable`.
		'''
		def __get__(self):
			cdef int resolution
			resolution = ddjvu_page_get_resolution(<ddjvu_page_t*> self.ddjvu_job)
			if resolution == 0:
				raise NotAvailable
			else:
				return resolution

	property gamma:
		'''
		Return the gamma of the display for which this page was designed.

		Before receiving a `PageInfoMessage`, return a meaningless but plausible value.
		'''
		def __get__(self):
			return ddjvu_page_get_gamma(<ddjvu_page_t*> self.ddjvu_job)
	
	property version:
		'''
		Return the version of the DjVu file format.

		Before receiving a `PageInfoMessage`, return a meaningless but plausible value.
		'''
		def __get__(self):
			return ddjvu_page_get_version(<ddjvu_page_t*> self.ddjvu_job)

	property type:
		'''
		Returns the type of the page data. Possible values are:
		* PAGE_TYPE_UNKNOWN,
		* PAGE_TYPE_BITONAL, 
		* PAGE_TYPE_PHOTO,
		* PAGE_TYPE_COMPOUND.

		Before receiving a `PageInfoMessage`, raise `NotAvailable`.
		'''
		def __get__(self):
			cdef ddjvu_page_type_t type
			cdef int is_done
			is_done = self.is_done
			type = ddjvu_page_get_type(<ddjvu_page_t*> self.ddjvu_job)
			if <int> type == <int> DDJVU_PAGETYPE_UNKNOWN and not is_done:
				# XXX An unavoidable race condition
				raise NotAvailable
			return type

	property initial_rotation:
		'''
		Returns the counter-clockwise page rotation angle (in degrees)
		specified by the orientation flags in the DjVu file.

		Brain damage warning
		--------------------
		This is useful because ``maparea`` coordinates in the annotation chunks
		are expressed relative to the rotated coordinates whereas text
		coordinates in the hidden text data are expressed relative to the
		unrotated coordinates.
		'''
		def __get__(self):
			return 90 * <int> ddjvu_page_get_initial_rotation(<ddjvu_page_t*> self.ddjvu_job)

	property rotation:
		'''
		The counter-clockwise rotation angle (in degrees) for the page. The
		rotation is automatically taken into account by `render(...)` method
		and `width` and `height` properties. 
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
				raise ValueError
			ddjvu_page_set_rotation(<ddjvu_page_t*> self.ddjvu_job, rotation)
	
		def __del__(self):
			ddjvu_page_set_rotation(<ddjvu_page_t*> self.ddjvu_job, ddjvu_page_get_initial_rotation(<ddjvu_page_t*> self.ddjvu_job))

	def render(self, int mode, page_rect, render_rect, PixelFormat pixel_format not None, unsigned int row_alignment = 0):
		'''
		J.render(mode, page_rect, render_rect, pixel_format, row_alignment=1) -> data.

		Render a segment of a page with arbitrary scale. `mode` indicates
		what image layers should be rendered:
		`RENDER_COLOR`
			color page or stencil
		`RENDER_BLACK`
			stencil or color page
		`RENDER_COLOR_ONLY`
			color page or fail
		`RENDER_MASK_ONLY`
			stencil or fail
		`RENDER_BACKGROUND`
			color background layer
		`RENDER_FOREGROUND`
			foreground background layer

		Conceptually this method renders the full page into a rectangle
		`page_rect` and copies the pixels specified by rectangle
		`render_rect` into a buffer. The actual code is much more efficient
		than that.
		
		`pixel_format` specifies the expected pixel format. Each row will start
		at `row_alignment` bytes boundary.
		
		This method makes a best effort to compute an image that reflects the
		most recently decoded data. It might raise `NotAvailable` to indicate
		that no image could be computed at this point.
		'''
		cdef ddjvu_rect_t c_page_rect
		cdef ddjvu_rect_t c_render_rect
		cdef size_t buffer_size
		cdef unsigned long row_size
		cdef int bpp
		cdef char* buffer
		(c_page_rect.x, c_page_rect.y, c_page_rect.w, c_page_rect.h) = page_rect
		(c_render_rect.x, c_render_rect.y, c_render_rect.w, c_render_rect.h) = render_rect
		row_size = calculate_row_size(c_render_rect.w, row_alignment, pixel_format._bpp)
		buffer = allocate_image_buffer(row_size, c_render_rect.h, &buffer_size)
		try:
			if ddjvu_page_render(<ddjvu_page_t*> self.ddjvu_job, mode, &c_page_rect, &c_render_rect, pixel_format.ddjvu_format, row_size, buffer) == 0:
				raise NotAvailable
			return charp_to_string(buffer, buffer_size)
		finally:
			py_free(buffer)

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
		if kwargs.get('sentinel') is not the_sentinel:
			raise_instantiation_error(type(self))
		self._context = None
		self.ddjvu_job = NULL
		self._queue = Queue()
	
	cdef object __init(self, Context context, ddjvu_job_t *ddjvu_job):
		# Assumption: `loft_lock` is already acquired. 
		if context is None:
			raise SystemError
		self._context = context
		self.ddjvu_job = ddjvu_job
		_job_loft.add(self)
		_job_weak_loft[<long> ddjvu_job] = self
	
	cdef object __clear(self):
		loft_lock.acquire()
		try:
			_job_loft.discard(self)
		finally:
			loft_lock.release()

	property status:
		'''
		Return a `JobException` subclass indicating the job status.
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
		J.wait().

		Wait until the job is done.
		XXX
		'''
		while not ddjvu_job_done(self.ddjvu_job):
			self._context.handle_job_message(self._queue.get())

	def stop(self):
		'''
		J.stop().

		Attempt to cancel the job.
		
		This is a best effort method. There no guarantee that the job will
		actually stop.
		'''
		ddjvu_job_stop(self.ddjvu_job)

	def get_message(self, wait = True):
		'''
		J.get_message(wait=True) -> a `Message` or `None`.

		Get message from the internal job queue.
		Return `None` if `wait` is false and no message is available.
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
		loft_lock.acquire()
		try:
			result = _job_weak_loft.get(<long> ddjvu_job)
		finally:
			loft_lock.release()
	return result

cdef class AffineTransform:

	'''
	AffineTransform((x0, y0, w0, h0), (x1, y0, w1, h1)) 
	  -> an affine coordinate transformation.

	The object represents an affine coordinate transformation that maps points
	from rectangle `(x0, y0, w0, h0)` to rectangle `(x1, y0, w1, h1)`.
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
		A.rotate(n).

		Rotate the output rectangle counter-clockwise by <n> degrees. 
		'''
		if n % 90:
			raise ValueError
		else:
			ddjvu_rectmapper_modify(self.ddjvu_rectmapper, n/90, 0, 0)

	def __call__(self, value):
		cdef ddjvu_rect_t rect
		next = iter(value).next
		try:
			rect.x = next()
			rect.y = next()
		except StopIteration:
			raise ValueError
		try:
			rect.w = next()
		except StopIteration:
			ddjvu_map_point(self.ddjvu_rectmapper, &rect.x, &rect.y)
			return (rect.x, rect.y)
		try:
			rect.h = next()
		except StopIteration:
			raise ValueError
		try:
			next()
		except StopIteration:
			pass
		else:
			raise ValueError
		ddjvu_map_rect(self.ddjvu_rectmapper, &rect)
		return (rect.x, rect.y, int(rect.w), int(rect.h))

	def apply(self, value):
		'''
		A.apply((x0, y0)) -> (x1, y1).
		A.apply((x0, y0, w0, h0)) -> (x1, y1, w1, h1).

		Apply the coordinate transform to a point or a rectangle.
		'''
		return self(value)

	def inverse(self, value):
		'''
		A.inverse((x0, y0)) -> (x1, y1).
		A.inverse((x0, y0, w0, h0)) -> (x1, y1, w1, h1).

		Apply the inverse coordinate transform to a point or a rectangle.
		'''
		cdef ddjvu_rect_t rect
		next = iter(value).next
		try:
			rect.x = next()
			rect.y = next()
		except StopIteration:
			raise ValueError
		try:
			rect.w = next()
		except StopIteration:
			ddjvu_unmap_point(self.ddjvu_rectmapper, &rect.x, &rect.y)
			return (rect.x, rect.y)
		try:
			rect.h = next()
		except StopIteration:
			raise ValueError
		try:
			next()
		except StopIteration:
			pass
		else:
			raise ValueError
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
		if kwargs.get('sentinel') is not the_sentinel:
			raise_instantiation_error(type(self))
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
		Return the concerned `Context`.
		'''
		def __get__(self):
			return self._context

	property document:
		'''
		Return the concerned `Document` or None.
		'''
		def __get__(self):
			return self._document

	property page_job:
		'''
		Return the concerned `PageJob` or None.
		'''
		def __get__(self):
			return self._page_job

	property job:
		'''
		Return the concerned `Job` or None.
		'''
		def __get__(self):
			return self._job

cdef class ErrorMessage(Message):
	'''
	An `ErrorMessage` is generated whenever the decoder or the DDJVU API
	encounters an error condition. All errors are reported as error messages
	because they can occur asynchronously.
	'''

	cdef object __init(self):
		Message.__init(self)
		self._message = self.ddjvu_message.m_error.message
		self._location = \
		(
			self.ddjvu_message.m_error.function,
			self.ddjvu_message.m_error.filename,
			self.ddjvu_message.m_error.lineno
		)

	property message:
		'''
		Return the actual error message, as text.
		'''
		def __get__(self):
			return self._message
	
	property location:
		'''
		Return the place (a `(function, filename, line_no)` tuple) where the
		error was detected.
		'''
		def __get__(self):
			return self._location

	def __str__(self):
		return self.message

	def __repr__(self):
		return '<%s.%s: %r at %r>' % (self.__class__.__module__, self.__class__.__name__, self.message, self.location)

cdef class InfoMessage(Message):
	'''
	A `InfoMessage` provides informational text indicating the progress of the
	decoding process. This might be displayed in the browser status bar.
	'''

	cdef object __init(self):
		Message.__init(self)
		self._message = self.ddjvu_message.m_error.message
	
	property message:
		'''
		Return the actual information message, as text.
		'''
		def __get__(self):
			return self._message
	
cdef class Stream:
	'''
	Data stream.

	Use `new_stream_message.stream` to obtain instances of this class.
	'''

	def __cinit__(self, Document document not None, int streamid, **kwargs):
		if kwargs.get('sentinel') is not the_sentinel:
			raise_instantiation_error(type(self))
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
		S.abort().

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

	def read(self, size = None):
		'''
		S.read([size])

		Raise `IOError`. (This method is provided solely to implement Python's
		file-like interface.)
		'''
		raise IOError
	
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
			string_to_charp_and_size(data, &raw_data, &length)
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
	A `NewStreamMessage` is generated whenever the decoder needs to access raw
	DjVu data. The caller must then provide the requested data using the
	`.stream` file-like object.
	
	In the case of indirect documents, a single decoder might simultaneously
	request several streams of data.
	
	'''

	cdef object __init(self):
		Message.__init(self)
		self._stream = Stream(self.document, self.ddjvu_message.m_newstream.streamid, sentinel = the_sentinel)
		self._name = self.ddjvu_message.m_newstream.name
		self._uri = self.ddjvu_message.m_newstream.url

	property stream:
		'''
		Return the concerned `Stream`.
		'''
		def __get__(self):
			return self._stream
	
	property name:
		'''
		The first `NewStreamMessage` message always has `.name` set to None.
		It indicates that the decoder needs to access the data in the main DjVu
		file.
		
		Further NewStreamMessage` messages messages are generated to access the
		auxiliary files of indirect or indexed DjVu documents. `.name` then
		provides the base name of the auxiliary file.
		'''
		def __get__(self):
			return self._name
	
	property uri:
		'''
		Return the requrested URI.

		URI is is set according to the `uri` argument provided to function
		`Context.new_document()`. The first `NewMessageStream` message always
		contain the URI passed to `Context.new_documnet()`. Subsequent
		`NewMessageStream`messages contain the URI of the auxiliary files for
		indirect or indexed DjVu documents.
		'''
		def __get__(self):
			return self._uri

cdef class DocInfoMessage(Message):
	'''
	A `DocInfoMessage` indicates that basic information about the document has
	been obtained and decoded. Not much can be done before this happens.
	
	Call `Document.decoding_status()` to determine whether the operation was
	successful.
	'''

cdef class PageInfoMessage(Message):
	'''
	The page decoding process generates a `PageInfoMessage`:
	- when basic page information is available and 
	  before any `RelayoutMessage` or `RedisplayMessage`,
	- when the page decoding thread terminates.
	You can distinguish both cases using `PageJob.decoding_status()`.

	A `PageInfoMessage` may be also generated as a consequence of reading
	`Page.info` and `Page.dump` properties. 
	'''

cdef class RelayoutMessage(Message):
	'''
	A `RelayoutMessage` is generated when a DjVu viewer should recompute the
	layout of the page viewer because the page size and resolution information
	has been updated.
	'''

cdef class RedisplayMessage(Message):
	'''
	A `RedisplayMessage` is generated when a DjVu viewer should call
	`PageJob.render()` and redisplay the page. This happens, for instance, when
	newly decoded DjVu data provides a better image.
	'''

cdef class ChunkMessage(Message):
	'''
	XXX
	'''

cdef class ThumbnailMessage(Message):
	'''
	XXX
	'''

	cdef object __init(self):
		Message.__init(self)
		self._page_no = self.ddjvu_message.m_thumbnail.pagenum
	
	property n:
		'''
		XXX
		'''
		def __get__(self):
			return self._page_no

cdef class ProgressMessage(Message):
	'''
	XXX
	'''

	cdef object __init(self):
		Message.__init(self)
		self._percent = self.ddjvu_message.m_progress.percent
		self._status = self.ddjvu_message.m_progress.status
	
	property percent:
		'''
		XXX
		'''
		def __get__(self):
			return self._percent
	
	property status:
		'''
		XXX
		'''
		def __get__(self):
			return self._status

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

cdef JobException_from_c(ddjvu_status_t code):
	try:
		return JOB_EXCEPTION_MAP[code]
	except KeyError:
		raise SystemError

class JobException(Exception):
	'''
	XXX
	'''

class JobNotDone(JobException):
	'''
	XXX
	'''

class JobNotStarted(JobNotDone):
	'''
	XXX
	'''

class JobStarted(JobNotDone):
	'''
	XXX
	'''

class JobDone(JobException):
	'''
	XXX
	'''

class JobOK(JobDone):
	'''
	XXX
	'''

class JobFailed(JobDone):
	'''
	XXX
	'''

class JobStopped(JobFailed):
	'''
	XXX
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
	XXX
	'''

	def __cinit__(self, Document document not None):
		self._document = document
		self._sexpr = wrap_sexpr(document, ddjvu_document_get_outline(document.ddjvu_document))
	
	property sexpr:
		'''
		XXX
		'''
		def __get__(self):
			return self._sexpr()
	
	def __repr__(self):
		return '%s.%s(%r)' % (self.__class__.__module__, self.__class__.__name__, self._document)

cdef class Annotations:
	'''
	XXX
	'''

	def __cinit__(self, *args, **kwargs):
		if typecheck(self, DocumentAnnotations):
			return
		if typecheck(self, PageAnnotations):
			return
		raise_instantiation_error(type(self))

	property sexpr:
		'''
		Return the associated S-expression.
		'''
		def __get__(self):
			return self._sexpr()
	
	property background_color:
		'''
		XXX
		'''
		def __get__(self):
			cdef char* result
			result = ddjvu_anno_get_bgcolor(self._sexpr._cexpr)
			if result == NULL:
				return
			return result

	property zoom:
		'''
		XXX
		'''
		def __get__(self):
			cdef char* result
			result = ddjvu_anno_get_zoom(self._sexpr._cexpr)
			if result == NULL:
				return
			return result

	property mode:
		'''
		XXX
		'''
		def __get__(self):
			cdef char* result
			result = ddjvu_anno_get_mode(self._sexpr._cexpr)
			if result == NULL:
				return
			return result

	property horizontal_align:
		'''
		XXX
		'''
		def __get__(self):
			cdef char* result
			result = ddjvu_anno_get_horizalign(self._sexpr._cexpr)
			if result == NULL:
				return
			return result

	property vertical_align:
		'''
		XXX
		'''
		def __get__(self):
			cdef char* result
			result = ddjvu_anno_get_vertalign(self._sexpr._cexpr)
			if result == NULL:
				return
			return result
	
	property hyperlinks:
		'''
		XXX
		'''
		def __get__(self):
			return Hyperlinks(self)
	
	property metadata:
		'''
		XXX
		'''
		def __get__(self):
			return Metadata(self)

cdef class DocumentAnnotations(Annotations):
	'''
	XXX
	'''

	def __cinit__(self, Document document not None, compat = True):
		self._document = document
		self._sexpr = wrap_sexpr(document, ddjvu_document_get_anno(document.ddjvu_document, compat))

	property document:
		'''
		Return the concerned `Document`.
		'''
		def __get__(self):
			return self._document
	
cdef class PageAnnotations(Annotations):

	def __cinit__(self, Page page not None):
		self._document = page._document
		self._page = page
		self._sexpr = wrap_sexpr(page._document, ddjvu_document_get_pageanno(page._document.ddjvu_document, page._n))
	
	property page:
		'''
		XXX
		'''
		def __get__(self):
			return self._page

	property sexpr:
		'''
		Return the associated S-expression.
		'''
		def __get__(self):
			return self._sexpr()

TEXT_DETAILS_PAGE = 'page'
TEXT_DETAILS_REGION = 'region'
TEXT_DETAILS_PARAGRAPH = 'para'
TEXT_DETAILS_LINE = 'line'

cdef class PageText:
	'''
	XXX
	'''

	def __cinit__(self, Page page not None, details = TEXT_DETAILS_LINE):
		if not is_string(details):
			raise TypeError
		if details not in (TEXT_DETAILS_PAGE, TEXT_DETAILS_REGION, TEXT_DETAILS_PARAGRAPH, TEXT_DETAILS_LINE):
			raise ValueError
		self._page = page
		self._sexpr = wrap_sexpr(page._document, ddjvu_document_get_pagetext(page._document.ddjvu_document, page._n, details))
	
	property page:
		'''
		XXX
		'''
		def __get__(self):
			return self._page

	property sexpr:
		'''
		Return the associated S-expression.
		'''
		def __get__(self):
			return self._sexpr()

cdef class Hyperlinks:
	'''
	XXX
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
				self._sexpr.append(wrap_sexpr(annotations._document, current[0]))
				current = current + 1
		finally:
			libc_free(all)
	
	def __len__(self):
		return len(self._sexpr)
	
	def __getitem__(self, Py_ssize_t n):
		return self._sexpr[n]()

cdef class Metadata:
	'''
	XXX
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
				keys.append(unicode(wrap_sexpr(annotations._document, current[0])()))
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
		return self._keys
	
	def iterkeys(self):
		return iter(self)

	def __iter__(self):
		return iter(self._keys)
	
	def has_key(self, k):
		return k in self
	
	def __contains__(self, k):
		return k in self._keys
	
__author__ = 'Jakub Wilk <ubanus@users.sf.net>'
__version__ = '%s/%d' % (PYTHON_DJVULIBRE_VERSION, DDJVU_VERSION)

# vim:ts=4 sw=4 noet ft=pyrex
