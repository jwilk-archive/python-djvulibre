# Copyright (c) 2007, 2008 Jakub Wilk <ubanus@users.sf.net>

include 'common.pxi'

import weakref
import thread
from Queue import Queue, Empty

cdef object the_sentinel
the_sentinel = object()

cdef object _context_loft, _document_loft, _job_loft, loft_lock
_context_loft = {}
_document_loft = {} # TODO: remove when decoding is done
_job_loft = {} # TODO: remove when decoding is done
_page_job_loft = {} # TODO: remove when decoding is done
loft_lock = thread.allocate_lock()

DDJVU_VERSION = ddjvu_code_get_version()

DOCUMENT_TYPE_UNKNOWN = DDJVU_DOCTYPE_UNKNOWN
DOCUMENT_TYPE_SINGLE_PAGE = DDJVU_DOCTYPE_SINGLEPAGE
DOCUMENT_TYPE_BUNDLED = DDJVU_DOCTYPE_BUNDLED
DOCUMENT_TYPE_INDIRECT = DDJVU_DOCTYPE_INDIRECT
DOCUMENT_TYPE_OLD_BUNDLED = DDJVU_DOCTYPE_OLD_BUNDLED
DOCUMENT_TYPE_OLD_INDEXED = DDJVU_DOCTYPE_OLD_INDEXED

class NotAvailable(Exception):
	pass

class DjVuLibreBug(Exception):
	
	def __init__(self, debian_bug_no):
		Exception.__init__(
			self,
			'A DjVuLibre bug has been encountered.\n'
			'See <http://bugs.debian.org/%d> for details.\n'
			'Please upgrade your DjVuLibre.' % (debian_bug_no,)
		)

cdef class DocumentExtension:

	property document:
		def __get__(self):
			return self._document_weakref()
	
cdef class DocumentPages(DocumentExtension):

	def __cinit__(self, Document document not None, object sentinel):
		if sentinel is not the_sentinel:
			raise_instantiation_error(type(self))
		import weakref
		self._document_weakref = weakref.ref(document)
	
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

	def __cinit__(self, Document document not None, int n):
		self._document = document
		self._n = n

	property document:
		def __get__(self):
			return self._document
	
	property n:
		def __get__(self):
			return self._n
	
	property thumbnail:
		def __get__(self):
			return Thumbnail(self)

	property info:
		def __get__(self):
			cdef ddjvu_status_t status
			cdef PageInfo page_info
			page_info = PageInfo(self._document, sentinel = the_sentinel)
			while True:
				status = ddjvu_document_get_pageinfo(self._document.ddjvu_document, self._n, &page_info.ddjvu_pageinfo)
				ex = JobException_from_c(status)
				if ex == JobOK:
					# FIXME: fix concurrency issues
					return page_info
				else:
					raise ex

	property dump:
		'''
		Return a text describing the contents of the page using the same format
		as the ``djvudump`` command. 

		If the information is not available, raise ``NotAvailable`` exception.
		Then, ``PageInfoMessage`` messages with empty ``page_job`` may be
		emitted.
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
		cdef PageJob job
		loft_lock.acquire()
		try:
			job = PageJob(sentinel = the_sentinel)
			job.__init(self._document._context, <ddjvu_job_t*>ddjvu_page_create_by_pageno(self._document.ddjvu_document, self._n))
		finally:
			loft_lock.release()
		if wait:
			job.wait()
		return job
	
	property annotations:
		def __get__(self):
			return PageAnnotations(self)
	
	property text:
		def __get__(self):
			return PageText(self)

cdef class Thumbnail:

	def __cinit__(self, Page page not None):
		self._page = page
	
	property page:
		def __get__(self):
			return self._page
	
	property status:
		def __get__(self):
			return JobException_from_c(ddjvu_thumbnail_status(self._page._document.ddjvu_document, self._page._n, 0))
	
	def calculate(self):
		return JobException_from_c(ddjvu_thumbnail_status(self._page._document.ddjvu_document, self._page._n, 1))

	def render(self, size, PixelFormat pixel_format not None, unsigned long row_alignment = 0, dry_run = False):
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
				return (w, h), pybuffer
			else:
				return None
		finally:
			py_free(buffer)

cdef class DocumentFiles(DocumentExtension):

	def __cinit__(self, Document document not None, object sentinel):
		if sentinel is not the_sentinel:
			raise_instantiation_error(type(self))
		import weakref
		self._document_weakref = weakref.ref(document)
	
	def __len__(self):
		return ddjvu_document_get_filenum((<Document>self.document).ddjvu_document)

	def __getitem__(self, key):
		return File(self.document, key, the_sentinel)

cdef class File:

	def __cinit__(self, Document document not None, int n, object sentinel):
		if sentinel is not the_sentinel:
			raise_instantiation_error(type(self))
		self._document = document
		self._n = n
	
	property document:
		def __get__(self):
			return self._document

	property n:
		def __get__(self):
			return self._n

	property info:
		def __get__(self):
			cdef ddjvu_status_t status
			cdef FileInfo file_info
			file_info = FileInfo(self._document, sentinel = the_sentinel)
			while True:
				status = ddjvu_document_get_fileinfo(self._document.ddjvu_document, self._n, &file_info.ddjvu_fileinfo)
				ex = JobException_from_c(status)
				if ex == JobOK:
					# FIXME: fix concurrency issues
					return file_info
				else:
					raise ex

	property dump:
		'''
		Return a text describing the contents of the file using the same format
		as the ``djvudump`` command. 

		If the information is not available, raise ``NotAvailable`` exception.
		Then, ``PageInfoMessage`` messages with empty ``page_job`` may be
		emitted.
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
	from itertools import imap
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

	def __cinit__(self, **kwargs):
		self._file = None
	
cdef class Document:

	def __cinit__(self, **kwargs):
		self.ddjvu_document = NULL
		if kwargs.get('sentinel') is not the_sentinel:
			raise_instantiation_error(type(self))
		self._pages = DocumentPages(self, sentinel = the_sentinel)
		self._files = DocumentFiles(self, sentinel = the_sentinel)
		self._context = None
		self._queue = Queue()
	
	cdef object __init(self, Context context, ddjvu_document_t *ddjvu_document):
		assert context != None and ddjvu_document != NULL
		self.ddjvu_document = ddjvu_document
		self._context = context
		_document_loft[<long> ddjvu_document] = self

	property status:
		def __get__(self):
			return JobException_from_c(ddjvu_document_decoding_status(self.ddjvu_document))

	property is_error:
		def __get__(self):
			return bool(ddjvu_document_decoding_error(self.ddjvu_document))
	
	property is_done:
		def __get__(self):
			return bool(ddjvu_document_decoding_done(self.ddjvu_document))

	property type:
		def __get__(self):
			return ddjvu_document_get_type(self.ddjvu_document)

	property pages:
		def __get__(self):
			return self._pages
	
	property files:
		def __get__(self):
			return self._files
	
	property outline:
		def __get__(self):
			return DocumentOutline(self)
	
	property annotations:
		def __get__(self):
			return DocumentAnnotations(self)

	def __dealloc__(self):
		if self.ddjvu_document == NULL:
			return
		ddjvu_document_release(self.ddjvu_document)
	
	def save(self, file = None, pages = None, indirect = None, wait = True):
		# XXX WARNING XXX
		# XXX Due to a DjVuLibre (<= 3.5.20) bug, this method may be broken.
		# XXX See <http://bugs.debian.org/bug=467282> for details.
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
			from os import devnull
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
		# XXX WARNING XXX
		# XXX Due to a DjVuLibre (<= 3.5.20) bug, this method may be broken.
		# XXX See <http://bugs.debian.org/469122> for details.
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

	def wait(self):
		while not ddjvu_document_decoding_done(self.ddjvu_document):
			self._context.handle_document_message(self._queue.get())

	def get_message(self, wait = True):
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
		result = _document_loft.get(<long> ddjvu_document)
	return result

cdef class PageInfo:

	def __cinit__(self, Document document not None, **kwargs):
		if kwargs.get('sentinel') is not the_sentinel:
			raise_instantiation_error(type(self))
		self._document = document
	
	property document:
		def __get__(self):
			return self._document
	
	property width:
		def __get__(self):
			return self.ddjvu_pageinfo.width
	
	property height:
		def __get__(self):
			return self.ddjvu_pageinfo.height
	
	property dpi:
		def __get__(self):
			return self.ddjvu_pageinfo.dpi
	
	property rotation:
		def __get__(self):
			return self.ddjvu_pageinfo.rotation * 90

	property version:
		def __get__(self):
			return self.ddjvu_pageinfo.version

cdef class FileInfo:

	def __cinit__(self, Document document not None, **kwargs):
		if kwargs.get('sentinel') is not the_sentinel:
			raise_instantiation_error(type(self))
		self._document = document
	
	property document:
		def __get__(self):
			return self._document
	
	property type:
		def __get__(self):
			return charp_to_string(&self.ddjvu_fileinfo.type, 1)
	
	property npage:
		def __get__(self):
			if self.ddjvu_fileinfo.pageno < 0:
				return None
			else:
				return self.ddjvu_fileinfo.pageno
	
	property size:
		def __get__(self):
			if self.ddjvu_fileinfo.size < 0:
				return None
			else:
				return self.ddjvu_fileinfo.size
	
	property id:
		def __get__(self):
			cdef char* result
			result = <char*> self.ddjvu_fileinfo.id
			if result == NULL:
				return None
			else:
				return decode_utf8(result)

	property name:
		def __get__(self):
			cdef char* result
			result = <char*> self.ddjvu_fileinfo.name
			if result == NULL:
				return None
			else:
				return decode_utf8(result)

	property title:
		def __get__(self):
			cdef char* result
			result = <char*> self.ddjvu_fileinfo.title
			if result == NULL:
				return None
			else:
				return decode_utf8(result)

class FileURI(str):
	pass

cdef class Context:

	def __cinit__(self, argv0 = None):
		if argv0 is None:
			from sys import argv
			argv0 = argv[0]
		loft_lock.acquire()
		try:
			self.ddjvu_context = ddjvu_context_create(argv0)
			if self.ddjvu_context == NULL:
				raise MemoryError
			_context_loft[<long> self.ddjvu_context] = self
		finally:
			loft_lock.release()
		self._queue = Queue()
		thread.start_new_thread(Context._message_distributor, (self, the_sentinel))
	
	def _message_distributor(self, sentinel):
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
			message = Message_from_c(ddjvu_message)
			ddjvu_message_pop(self.ddjvu_context)
			if message is None:
				raise SystemError
			# XXX Order of branches below is *crucial*. Do not change.
			if message._job is not None:
				job = message._job
				job._queue.put(message)
			elif message._page_job is not None:
				page_job = self._page_job
				page_job._queue.put(message)
			elif message._document is not None:
				document = message._document
				document._queue.put(message)
			else:
				self._queue.put(message)

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
		pass
	
	def handle_job_message(self, message):
		pass
	
	def handle_document_message(self, message):
		pass

	def get_message(self, wait = True):
		try:
			return self._queue.get(wait)
		except Empty:
			return

	def new_document(self, uri, cache = True):
		cdef Document document
		cdef ddjvu_document_t* ddjvu_document
		loft_lock.acquire()
		try:
			if typecheck(uri, FileURI):
				ddjvu_document = ddjvu_document_create_by_filename(self.ddjvu_context, uri, cache)
			else:
				ddjvu_document = ddjvu_document_create(self.ddjvu_context, uri, cache)
			if ddjvu_document == NULL:
				return None
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

		def __get__(self):
			return bool(self._row_order)

		def __set__(self, value):
			ddjvu_format_set_row_order(self.ddjvu_format, not not value)

	property y_top_to_bottom:

		def __get__(self):
			return bool(self._row_order)

		def __set__(self, value):
			ddjvu_format_set_y_direction(self.ddjvu_format, not not value)
	
	property bpp:
		def __get__(self):
			return self._bpp
	
	property dither_bpp:
		def __get__(self):
			return self._dither_bpp

		def __set__(self, int value):
			if (value > 0 and value < 64):
				ddjvu_format_set_ditherbits(self.ddjvu_format, value)
				self._dither_bpp = value
			else:
				raise ValueError
	
	property gamma:
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

	def __cinit__(self, unsigned int bpp = 8):
		cdef unsigned int params[4]
		if bpp != 8:
			raise ValueError
		self._bpp = self._dither_bpp = bpp
		self.ddjvu_format = ddjvu_format_create(DDJVU_FORMAT_GREY8, 0, NULL)

	def __repr__(self):
		return '%s.%s(bpp = %d)' % (self.__class__.__module__, self.__class__.__name__, self.bpp)

cdef class PixelFormatPalette(PixelFormat):

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
		from cStringIO import StringIO
		io = StringIO()
		io.write('%s.%s([' % (self.__class__.__module__, self.__class__.__name__))
		for i from 0 <= i < 215:
			io.write('0x%02x, ' % self._palette[i])
		io.write('0x%02x], bpp = %d)' % (self._palette[215], self.bpp))
		return io.getvalue()

cdef class PixelFormatPackedBits(PixelFormat):
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

	cdef object __init(self, Context context, ddjvu_job_t *ddjvu_job):
		Job.__init(self, context, ddjvu_job)
		_page_job_loft[<long> ddjvu_job] = self
	
	property width:
		'''
		Return the page width in pixels.

		Before receiving a ``PageInfoMessage``, raise ``NotAvailable``.
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

		Before receiving a ``PageInfoMessage``, raise ``NotAvailable``.
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

		Before receiving a ``PageInfoMessage``, raise ``NotAvailable``.
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

		Before receiving a ``PageInfoMessage``, return a meaningless but plausible value.
		'''
		def __get__(self):
			return ddjvu_page_get_gamma(<ddjvu_page_t*> self.ddjvu_job)
	
	property version:
		'''
		Return the version of the DjVu file format.

		Before receiving a ``PageInfoMessage``, return a meaningless but plausible value.
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

		Before receiving a ``PageInfoMessage``, raise ``NotAvailable``.
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
		def __get__(self):
			return 90 * <int> ddjvu_page_get_initial_rotation(<ddjvu_page_t*> self.ddjvu_job)

	property rotation:
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
		Render a segment of a page with arbitrary scale. ``mode`` indicates
		what image layers should be rendered. 
		
		Conceptually this method renders the full page into a rectangle
		``page_rect`` and copies the pixels specified by rectangle
		``render_rect`` into a buffer. The actual code is much more efficient
		than that.
		
		``pixel_format`` specifies the expected pixel format.
		``row_alignment`` XXX.
		
		This method makes a best effort to compute an image that reflects the
		most recently decoded data. It might raise ``NotAvailable`` to indicate
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
	cdef PageJob result
	if ddjvu_page == NULL:
		result = None
	else:
		loft_lock.acquire()
		try:
			result = _page_job_loft.get(<long> ddjvu_page)
		finally:
			loft_lock.release()
	return result

cdef class Job:

	def __cinit__(self, **kwargs):
		if kwargs.get('sentinel') is not the_sentinel:
			raise_instantiation_error(type(self))
		self._context = None
		self.ddjvu_job = NULL
		self._queue = Queue()
	
	cdef object __init(self, Context context, ddjvu_job_t *ddjvu_job):
		if context is None:
			raise SystemError
		self._context = context
		self.ddjvu_job = ddjvu_job
		_job_loft[<int> ddjvu_job] = self

	property status:
		def __get__(self):
			return JobException_from_c(ddjvu_job_status(self.ddjvu_job))

	property is_error:
		def __get__(self):
			return bool(ddjvu_job_error(self.ddjvu_job))
	
	property is_done:
		def __get__(self):
			return bool(ddjvu_job_done(self.ddjvu_job))

	def wait(self):
		while not ddjvu_job_done(self.ddjvu_job):
			self._context.handle_job_message(self._queue.get())

	def stop(self):
		ddjvu_job_stop(self.ddjvu_job)

	def get_message(self, wait = True):
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
			result = _job_loft.get(<long> ddjvu_job)
		finally:
			loft_lock.release()
	return result

cdef class AffineTransform:
	def __cinit__(self, input, output):
		cdef ddjvu_rect_t c_input
		cdef ddjvu_rect_t c_output
		self.ddjvu_rectmapper = NULL
		(c_input.x, c_input.y, c_input.w, c_input.h) = input
		(c_output.x, c_output.y, c_output.w, c_output.h) = output
		self.ddjvu_rectmapper = ddjvu_rectmapper_create(&c_input, &c_output)

	def rotate(self, int n):
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
		return self(value)

	def reverse(self, value):
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
		ddjvu_rectmapper_modify(self.ddjvu_rectmapper, 0, 1, 0)
	
	def mirror_y(self):
		ddjvu_rectmapper_modify(self.ddjvu_rectmapper, 0, 0, 1)

	def __dealloc__(self):
		if self.ddjvu_rectmapper != NULL:
			ddjvu_rectmapper_release(self.ddjvu_rectmapper)

cdef class Message:

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
		def __get__(self):
			return self._context

	property document:
		def __get__(self):
			return self._document

	property page_job:
		def __get__(self):
			return self._page_job

	property job:
		def __get__(self):
			return self._job

cdef class ErrorMessage(Message):

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
		def __get__(self):
			return self._message
	
	property location:
		def __get__(self):
			return self._location

	def __str__(self):
		return self.message

	def __repr__(self):
		return '<%s.%s: %r at %r>' % (self.__class__.__module__, self.__class__.__name__, self.message, self.location)

cdef class InfoMessage(Message):

	cdef object __init(self):
		Message.__init(self)
		self._message = self.ddjvu_message.m_error.message
	
	property message:
		def __get__(self):
			return self._message
	
cdef class Stream:

	def __cinit__(self, Document document not None, int streamid, **kwargs):
		if kwargs.get('sentinel') is not the_sentinel:
			raise_instantiation_error(type(self))
		self._streamid = streamid
		self._document = document
		self._open = 1

	def close(self):
		ddjvu_stream_close(self._document.ddjvu_document, self._streamid, 0)
		self._open = 0
	
	def abort(self):
		ddjvu_stream_close(self._document.ddjvu_document, self._streamid, 1)
		self._open = 0
	
	def flush(self):
		pass

	def read(self, size = None):
		raise IOError
	
	def write(self, data):
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

	cdef object __init(self):
		Message.__init(self)
		self._stream = Stream(self.document, self.ddjvu_message.m_newstream.streamid, sentinel = the_sentinel)
		self._name = self.ddjvu_message.m_newstream.name
		self._uri = self.ddjvu_message.m_newstream.url

	property stream:
		def __get__(self):
			return self._stream
	
	property name:
		def __get__(self):
			return self._name
	
	property uri:
		def __get__(self):
			return self._uri

cdef class DocInfoMessage(Message):
	pass

cdef class PageInfoMessage(Message):
	pass

cdef class RelayoutMessage(Message):
	pass

cdef class RedisplayMessage(Message):
	pass

cdef class ChunkMessage(Message):
	pass

cdef class ThumbnailMessage(Message):

	cdef object __init(self):
		Message.__init(self)
		self._page_no = self.ddjvu_message.m_thumbnail.pagenum
	
	property n:
		def __get__(self):
			return self._page_no

cdef class ProgressMessage(Message):

	cdef object __init(self):
		Message.__init(self)
		self._percent = self.ddjvu_message.m_progress.percent
		self._status = self.ddjvu_message.m_progress.status
	
	property percent:
		def __get__(self):
			return self._percent
	
	property status:
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
		return None
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
	pass

class JobNotDone(JobException):
	pass

class JobNotStarted(JobNotDone):
	pass

class JobStarted(JobNotDone):
	pass

class JobDone(JobException):
	pass

class JobOK(JobDone):
	pass

class JobFailed(JobDone):
	pass

class JobStopped(JobFailed):
	pass

JOB_EXCEPTION_MAP = \
{
	DDJVU_JOB_NOTSTARTED: JobNotStarted,
	DDJVU_JOB_STARTED: JobStarted,
	DDJVU_JOB_OK: JobOK,
	DDJVU_JOB_FAILED: JobFailed,
	DDJVU_JOB_STOPPED: JobStopped
}

cdef class _SexprWrapper:

	def __cinit__(self, document, sentinel):
		import weakref
		self._document_weakref = weakref.ref(document)
		if sentinel != the_sentinel:
			raise_instantiation_error(type(self))
	
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
	result = _SexprWrapper(document, the_sentinel)
	result._cexpr = cexpr
	return result

cdef class DocumentOutline:

	def __cinit__(self, Document document not None):
		self._document = document
		self._sexpr = wrap_sexpr(document, ddjvu_document_get_outline(document.ddjvu_document))
	
	property sexpr:
		def __get__(self):
			return self._sexpr()
	
	property document:
		def __get__(self):
			return self._document
	
	def __repr__(self):
		return '%s.%s(%r)' % (self.__class__.__module__, self.__class__.__name__, self._document)

cdef class Annotations:

	def __cinit__(self, *args, **kwargs):
		if typecheck(self, DocumentAnnotations):
			return
		if typecheck(self, PageAnnotations):
			return
		raise_instantiation_error(type(self))

	property sexpr:
		def __get__(self):
			return self._sexpr()
	
	property background_color:
		def __get__(self):
			cdef char* result
			result = ddjvu_anno_get_bgcolor(self._sexpr._cexpr)
			if result == NULL:
				return None
			return result

	property zoom:
		def __get__(self):
			cdef char* result
			result = ddjvu_anno_get_zoom(self._sexpr._cexpr)
			if result == NULL:
				return
			return result

	property mode:
		def __get__(self):
			cdef char* result
			result = ddjvu_anno_get_mode(self._sexpr._cexpr)
			if result == NULL:
				return
			return result

	property horizontal_align:
		def __get__(self):
			cdef char* result
			result = ddjvu_anno_get_horizalign(self._sexpr._cexpr)
			if result == NULL:
				return
			return result

	property vertical_align:
		def __get__(self):
			cdef char* result
			result = ddjvu_anno_get_vertalign(self._sexpr._cexpr)
			if result == NULL:
				return
			return result
	
	property hyperlinks:
		def __get__(self):
			return Hyperlinks(self)
	
	property metadata:
		def __get__(self):
			return Metadata(self)

cdef class DocumentAnnotations(Annotations):

	def __cinit__(self, Document document not None, compat = True):
		self._document = document
		self._sexpr = wrap_sexpr(document, ddjvu_document_get_anno(document.ddjvu_document, compat))

	property document:
		def __get__(self):
			return self._document
	
cdef class PageAnnotations(Annotations):

	def __cinit__(self, Page page not None):
		self._document = page._document
		self._page = page
		self._sexpr = wrap_sexpr(page._document, ddjvu_document_get_pageanno(page._document.ddjvu_document, page._n))
	
	property page:
		def __get__(self):
			return self._page

	property sexpr:
		def __get__(self):
			return self._sexpr()

TEXT_DETAILS_PAGE = 'page'
TEXT_DETAILS_REGION = 'region'
TEXT_DETAILS_PARAGRAPH = 'para'
TEXT_DETAILS_LINE = 'line'

cdef class PageText:

	def __cinit__(self, Page page not None, details = TEXT_DETAILS_LINE):
		if not is_string(details):
			raise TypeError
		if details not in (TEXT_DETAILS_PAGE, TEXT_DETAILS_REGION, TEXT_DETAILS_PARAGRAPH, TEXT_DETAILS_LINE):
			raise ValueError
		self._page = page
		self._sexpr = wrap_sexpr(page._document, ddjvu_document_get_pagetext(page._document.ddjvu_document, page._n, details))
	
	property page:
		def __get__(self):
			return self._page

	property sexpr:
		def __get__(self):
			return self._sexpr()

cdef class Hyperlinks:

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
		from djvu.sexpr import Symbol
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
__version__ = '0.1.1/%d' % DDJVU_VERSION

# vim:ts=4 sw=4 noet ft=pyrex
