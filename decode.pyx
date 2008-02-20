# Copyright (c) 2007, 2008 Jakub Wilk <ubanus@users.sf.net>

ctypedef int size_t

cdef extern from 'Python.h':
	int PyString_AsStringAndSize(object, char**, int*) except -1
	char* PyString_AsString(object) except NULL
	object PyString_FromStringAndSize(char *s, int len)
	void* PyMem_Malloc(size_t size)
	void PyMem_Free(void* buffer)

	int typecheck 'PyObject_TypeCheck'(object o, object type)
	int is_short_int 'PyInt_Check'(object o)
	int is_long_int 'PyLong_Check'(object o)
	int is_unicode 'PyUnicode_Check'(object o)

cdef int is_int(object o):
	return is_short_int(o) or is_long_int(o)

cdef extern from 'stdlib.h':
	void libc_free 'free'(void* ptr)

cdef extern from 'string.h':
	int strcmp(char *s1, char *s2)


cdef object the_sentinel
the_sentinel = object()


VERSION = ddjvu_code_get_version()

class InstantiationError(RuntimeError):
	pass


DOCUMENT_TYPE_UNKNOWN = DDJVU_DOCTYPE_UNKNOWN
DOCUMENT_TYPE_SINGLE_PAGE = DDJVU_DOCTYPE_SINGLEPAGE
DOCUMENT_TYPE_BUNDLED = DDJVU_DOCTYPE_BUNDLED
DOCUMENT_TYPE_INDIRECT = DDJVU_DOCTYPE_INDIRECT
DOCUMENT_TYPE_OLD_BUNDLED = DDJVU_DOCTYPE_OLD_BUNDLED
DOCUMENT_TYPE_OLD_INDEXED = DDJVU_DOCTYPE_OLD_INDEXED

cdef class DocumentExtension:

	property document:
		def __get__(self):
			return self._document_weakref()
	
cdef class DocumentPages(DocumentExtension):

	def __cinit__(self, Document document not None, object sentinel):
		if sentinel is not the_sentinel:
			raise InstantiationError
		import weakref
		self._document_weakref = weakref.ref(document)
	
	def __len__(self):
		return ddjvu_document_get_pagenum((<Document>self.document).ddjvu_document)

	def __getitem__(self, key):
		if is_int(key):
			if key < 0:
				raise ValueError
			return PageNth(self.document, key, the_sentinel)
		elif is_unicode(key):
			return PageById(self.document, key, the_sentinel)
		else:
			raise TypeError

cdef class Page:

#	def __cinit__(self):
#		pass
#	FIXME

	property document:
		def __get__(self):
			return self._document
	
	property n:
		def __get__(self):
			raise NotImplementedError

	property id:
		def __get__(self):
			raise NotImplementedError

	property info:
		def __get__(self):
			raise NotImplementedError
	
	property dump:
		def __get__(self):
			raise NotImplementedError

	def decode(self, wait = True):
		raise NotImplementedError

cdef class PageNth(Page):

	def __cinit__(self, Document document not None, int n, object sentinel):
		if sentinel is not the_sentinel:
			raise InstantiationError
		self._document = document
		self._n = n

	property n:
		def __get__(self):
			return self._n

	property info:
		def __get__(self):
			cdef ddjvu_status_t status
			cdef PageInfo page_info
			page_info = PageInfo(self._document, sentinel = the_sentinel)
			while True:
				status = ddjvu_document_get_pageinfo(self._document.ddjvu_document, self._n, &page_info.ddjvu_pageinfo)
				ex = JobException_from_c(status)
				if issubclass(ex, JobNotDone):
					# FIXME: fix concurrency issues
					try:
						self._document._context.handle_messages(wait = True)
					except NotImplementedError:
						raise ex
				elif ex == JobOK:
					return page_info
				else:
					raise ex

	property dump:
		def __get__(self):
			cdef char* s
			s = ddjvu_document_get_pagedump(self._document.ddjvu_document, self._n)
			if s == NULL:
				return None
				# FIXME?
			else:
				result = s.decode('UTF-8')
				libc_free(s)

	def decode(self, wait = True):
		page_job = PageJob_from_c(ddjvu_page_create_by_pageno(self._document.ddjvu_document, self._n), self._document._context)
		if wait:
			page_job.wait()
		return page_job

cdef class PageById(Page):
	
	def __cinit__(self, Document document not None, object id, object sentinel):
		if sentinel is not the_sentinel:
			raise InstantiationError
		self._document = document
		self._id = id

	property id:
		def __get__(self):
			return self._id
	
	def decode(self):
		return PageJob_from_c(ddjvu_page_create_by_pageid(
			self._document.ddjvu_document,
			PyString_AsString(self._id.decode('UTF-8'))
		), self._document._context)

cdef class DocumentFiles(DocumentExtension):

	def __cinit__(self, Document document not None, object sentinel):
		if sentinel is not the_sentinel:
			raise InstantiationError
		import weakref
		self._document_weakref = weakref.ref(document)
	
	def __len__(self):
		return ddjvu_document_get_filenum((<Document>self.document).ddjvu_document)

	def __getitem__(self, key):
		return File(self.document, key, the_sentinel)

cdef class File:

	def __cinit__(self, Document document not None, int n, object sentinel):
		if sentinel is not the_sentinel:
			raise InstantiationError
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
				if issubclass(ex, JobNotDone):
					try:
						# FIXME: fix concurrency issues
						self._document._context.handle_messages(wait = True)
					except NotImplementedError:
						raise ex
				elif ex == JobOK:
					return file_info
				else:
					raise ex

	property dump:
		def __get__(self):
			cdef char* s
			s = ddjvu_document_get_filedump(self._document.ddjvu_document, self._n)
			if s == NULL:
				return None
				# FIXME?
			else:
				result = s.decode('UTF-8')
				libc_free(s)

cdef class Document:

	def __cinit__(self, **kwargs):
		self.ddjvu_document = NULL
		if kwargs.get('sentinel') is not the_sentinel:
			raise InstantiationError
		self._pages = DocumentPages(self, sentinel = the_sentinel)
		self._files = DocumentFiles(self, sentinel = the_sentinel)

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

	def __dealloc__(self):
		if self.ddjvu_document == NULL:
			return
		# FIXME ddjvu_document_release(self.ddjvu_document)

cdef Document Document_from_c(ddjvu_document_t* ddjvu_document):
	cdef Document result
	if ddjvu_document == NULL:
		result = None
	else:
		result = Document(sentinel = the_sentinel)
		result.ddjvu_document = ddjvu_document
	return result


cdef class PageInfo:

	def __cinit__(self, Document document not None, **kwargs):
		if kwargs.get('sentinel') is not the_sentinel:
			raise InstantiationError
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
			raise InstantiationError
		self._document = document
	
	property document:
		def __get__(self):
			return self._document
	
	property type:
		def __get__(self):
			return PyString_FromStringAndSize(&self.ddjvu_fileinfo.type, 1)
	
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
				return result.decode('UTF-8')

	property name:
		def __get__(self):
			cdef char* result
			result = <char*> self.ddjvu_fileinfo.name
			if result == NULL:
				return None
			else:
				return result.decode('UTF-8')

	property title:
		def __get__(self):
			cdef char* result
			result = <char*> self.ddjvu_fileinfo.title
			if result == NULL:
				return None
			else:
				return result.decode('UTF-8')


class FileURI(str):
	pass

cdef class Context:

	def __cinit__(self, argv0 = None, **kwargs):
		if kwargs.get('sentinel') is the_sentinel:
			return
		if argv0 is None:
			from sys import argv
			argv0 = argv[0]
		self.ddjvu_context = ddjvu_context_create(argv0)
		if self.ddjvu_context == NULL:
			raise MemoryError
	
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
		raise NotImplementedError

	def handle_messages(self, wait):
		message = self.get_message(wait)
		while True:
			if message is None:
				return
			self.handle_message(message)
			message = self.get_message(wait = False)

	def get_message(self, wait = True):
		cdef ddjvu_message_t* ddjvu_message
		if wait:
			ddjvu_message = ddjvu_message_wait(self.ddjvu_context)
		else:
			ddjvu_message = ddjvu_message_peek(self.ddjvu_context)
			if ddjvu_message == NULL:
				return None
		message = Message_from_c(ddjvu_message)
		ddjvu_message_pop(self.ddjvu_context)
		return message

	def new_document(self, uri, cache = True):
		cdef Document document
		cdef ddjvu_document_t* ddjvu_document
		if typecheck(uri, FileURI):
			ddjvu_document = ddjvu_document_create_by_filename(self.ddjvu_context, uri, cache)
		else:
			ddjvu_document = ddjvu_document_create(self.ddjvu_context, uri, cache)
		document = Document_from_c(ddjvu_document)
		if document is not None:
			document._context = self
		return document

	def __iter__(self):
		return self

	def __next__(self):
		return self.get_message()

	def clear_cache(self):
		ddjvu_cache_clear(self.ddjvu_context)

	def __dealloc__(self):
		pass
		# FIXME ddjvu_context_release(self.ddjvu_context)

cdef Context Context_from_c(ddjvu_context_t* ddjvu_context):
	cdef Context result
	if ddjvu_context == NULL:
		result = None
	else:
		result = Context(sentinel = the_sentinel)
		result.ddjvu_context = ddjvu_context
	return result


RENDER_COLOR = DDJVU_RENDER_COLOR
RENDER_BLACK = DDJVU_RENDER_BLACK
RENDER_COLOR_ONLY = DDJVU_RENDER_COLORONLY
RENDER_MASK_ONLY = DDJVU_RENDER_MASKONLY
RENDER_BACKGROUND = DDJVU_RENDER_BACKGROUND
RENDER_FOREGROUND = DDJVU_RENDER_FOREGROUND

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
		raise InstantiationError
	
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
			if (_value >= 0.5 and value <= 5.0):
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

class RenderError(Exception):
	pass

cdef class PageJob(Job):
	
	property width:
		def __get__(self):
			cdef int width
			width = ddjvu_page_get_width(<ddjvu_page_t*> self.ddjvu_job)
			if width == 0:
				return None
				# FIXME?
			else:
				return width
	
	property height:
		def __get__(self):
			cdef int height
			height = ddjvu_page_get_height(<ddjvu_page_t*> self.ddjvu_job)
			if height == 0:
				return None
				# FIXME?
			else:
				return height

	property resolution:
		def __get__(self):
			cdef int resolution
			resolution = ddjvu_page_get_resolution(<ddjvu_page_t*> self.ddjvu_job)
			if resolution == 0:
				return None
				# FIXME?
			else:
				return resolution

	property gamma:
		def __get__(self):
			return ddjvu_page_get_gamma(<ddjvu_page_t*> self.ddjvu_job)
	
	property version:
		def __get__(self):
			return ddjvu_page_get_version(<ddjvu_page_t*> self.ddjvu_job)

	property type:
		def __get__(self):
			cdef ddjvu_page_type_t type
			type = ddjvu_page_get_type(<ddjvu_page_t*> self.ddjvu_job)
			if <int> type == <int> DDJVU_PAGETYPE_UNKNOWN:
				return None
				# FIXME?
			else:
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

	def render(self, int mode, page_rect, render_rect, PixelFormat pixel_format not None, unsigned long row_alignment):
		cdef ddjvu_rect_t c_page_rect
		cdef ddjvu_rect_t c_render_rect
		cdef size_t c_buffer_size
		cdef unsigned long row_size
		cdef int bpp
		cdef char* buffer
		(c_page_rect.x, c_page_rect.y, c_page_rect.w, c_page_rect.h) = page_rect
		(c_render_rect.x, c_render_rect.y, c_render_rect.w, c_render_rect.h) = render_rect
		bpp = pixel_format._bpp
		if bpp == 1:
			row_size = (c_render_rect.w + 7) >> 3
		elif bpp & 7 == 0:
			row_size = c_render_rect.w * (bpp >> 3)
		else:
			raise SystemError
		if row_alignment == 0:
			row_alignment = 1
		row_size = ((row_size + (row_alignment - 1)) / row_alignment) * row_alignment
		buffer_size = int(row_size) * int(c_render_rect.h)
		try:
			c_buffer_size = buffer_size
		except OverflowError:
			buffer = NULL
		else:
			buffer = <char*> PyMem_Malloc(buffer_size)
		if buffer == NULL:
			raise MemoryError('Unable to alocate %d bytes for an image buffer' % buffer_size)
		try:
			if ddjvu_page_render(<ddjvu_page_t*> self.ddjvu_job, mode, &c_page_rect, &c_render_rect, pixel_format.ddjvu_format, row_size, buffer) == 0:
				raise RenderError
			return PyString_FromStringAndSize(buffer, buffer_size)
		finally:
			PyMem_Free(buffer)

	def __dealloc__(self):
		pass
		# FIXME ddjvu_page_release(self.ddjvu_context)


cdef PageJob PageJob_from_c(ddjvu_page_t* ddjvu_page, Context context):
	cdef PageJob result
	if ddjvu_page == NULL:
		result = None
	else:
		result = PageJob(sentinel = the_sentinel)
		result.ddjvu_job = <ddjvu_job_t*> ddjvu_page
		result._context = context
	return result


cdef class Job:

	def __cinit__(self, **kwargs):
		if kwargs.get('sentinel') is not the_sentinel:
			raise InstantiationError
		self.ddjvu_job = NULL

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
			self._context.handle_messages(wait = True)

	def stop(self):
		ddjvu_job_stop(self.ddjvu_job)

	def __dealloc__(self):
		if self.ddjvu_job == NULL:
			return
		# XXX ddjvu_job_release(self.ddjvu_job)

cdef Job Job_from_c(ddjvu_job_t* ddjvu_job):
	cdef Job result
	if ddjvu_job == NULL:
		result = None
	else:
		result = Job(sentinel = the_sentinel)
		result.ddjvu_job = ddjvu_job
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
			raise InstantiationError
		self.ddjvu_message = NULL
	
	def __init(self):
		if self.ddjvu_message == NULL:
			raise SystemError
		self._context = Context_from_c(self.ddjvu_message.m_any.context)
		self._document = Document_from_c(self.ddjvu_message.m_any.document)
		self._page_job = PageJob_from_c(self.ddjvu_message.m_any.page, self._context)
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

	def __init(self):
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

	def __init(self):
		self._message = self.ddjvu_message.m_error.message
	
	property message:
		def __get__(self):
			return self._message
	
cdef class Stream:

	def __cinit__(self, Document document not None, int streamid, **kwargs):
		if kwargs.get('sentinel') is not the_sentinel:
			raise InstantiationError
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
		cdef int length
		if self._open:
			PyString_AsStringAndSize(data, &raw_data, &length)
			ddjvu_stream_write(self._document.ddjvu_document, self._streamid, raw_data, length)
		else:
			raise IOError('I/O operation on closed file')

	def __dealloc__(self):
		if <object>self._document is None:
			return
		if self._open:
			ddjvu_stream_close(self._document.ddjvu_document, self._streamid, 1)

cdef class NewStreamMessage(Message):

	def __init(self):
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

	def __init(self):
		Message.__init_(self)
		self._page_no = self._uri = self.ddjvu_message.m_thumbnail.pagenum
	
	property n:
		def __get__(self):
			return self._n

cdef class ProgressMessage(Message):
	pass

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

# vim:ts=4 sw=4 noet
