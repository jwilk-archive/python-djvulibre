# Copyright (c) 2007 Jakub Wilk <ubanus@users.sf.net>

cdef extern from 'Python.h':
	int PyString_AsStringAndSize(object, char**, int*) except -1
	char* PyString_AsString(object) except NULL
	object PyString_FromStringAndSize(char *s, int len)

cdef extern from 'stdlib.h':
	void libc_free 'free'(void* ptr)


cdef object the_sentinel
the_sentinel = object()


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

	def __new__(self, Document document not None, object sentinel):
		if sentinel is not the_sentinel:
			raise InstantiationError
		import weakref
		self._document_weakref = weakref.ref(document)
	
	def __len__(self):
		return ddjvu_document_get_pagenum((<Document>self.document).ddjvu_document)

	def __getitem__(self, key):
		if isinstance(key, (int, long)):
			if key < 0:
				raise ValueError
			return PageNth(self.document, key, the_sentinel)
		elif isinstance(key, unicode):
			return PageById(self.document, key, the_sentinel)
		else:
			raise TypeError

cdef class Page:

#	def __new__(self):
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

	def decode(self):
		raise NotImplementedError

cdef class PageNth(Page):

	def __new__(self, Document document not None, int n, object sentinel):
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
			status = ddjvu_document_get_pageinfo(self._document.ddjvu_document, self._n, &page_info.ddjvu_pageinfo)
			try:
				raise JobException_from_c(status)
			except JobOK:
				return page_info

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

	def decode(self):
		return PageJob_from_c(ddjvu_page_create_by_pageno(self._document.ddjvu_document, self._n))

cdef class PageById(Page):
	
	def __new__(self, Document document not None, object id, object sentinel):
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
		))

cdef class DocumentFiles(DocumentExtension):

	def __new__(self, Document document not None, object sentinel):
		if sentinel is not the_sentinel:
			raise InstantiationError
		import weakref
		self._document_weakref = weakref.ref(document)
	
	def __len__(self):
		return ddjvu_document_get_filenum((<Document>self.document).ddjvu_document)

	def __getitem__(self, key):
		return File(self.document, key, the_sentinel)

cdef class File:

	def __new__(self, Document document not None, int n, object sentinel):
		if sentinel is not the_sentinel:
			raise InstantiationError
		self._document = document
		self._n = n
	
	property document:
		def __get__(self):
			return self._document

	property n:
		def __get__(self):
			return n

	property info:
		def __get__(self):
			cdef ddjvu_status_t status
			cdef FileInfo file_info
			file_info = FileInfo(self._document, sentinel = the_sentinel)
			status = ddjvu_document_get_fileinfo(self._document.ddjvu_document, self._n, &file_info.ddjvu_fileinfo)
			try:
				raise JobException_from_c(status)
			except JobOK:
				return file_info

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

	def __new__(self, **kwargs):
		if kwargs.get('sentinel') is not the_sentinel:
			raise InstantiationError
		self.ddjvu_document = NULL
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

	def __new__(self, Document document not None, **kwargs):
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

	def __new__(self, Document document not None, **kwargs):
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

	def __new__(self, argv0 = None, **kwargs):
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
		if isinstance(uri, FileURI):
			ddjvu_document = ddjvu_document_create_by_filename(self.ddjvu_context, uri, cache)
		else:
			ddjvu_document = ddjvu_document_create(self.ddjvu_context, uri, cache)
		return Document_from_c(ddjvu_document)

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


cdef class PageJob:
	
	def __new__(self, **kwargs):
		if kwargs.get('sentinel') is not the_sentinel:
			raise InstantiationError
		self.ddjvu_page = NULL

cdef PageJob PageJob_from_c(ddjvu_page_t* ddjvu_page):
	cdef PageJob result
	if ddjvu_page == NULL:
		result = None
	else:
		result = PageJob(sentinel = the_sentinel)
		result.ddjvu_page = ddjvu_page
	return result


cdef class Job:

	def __new__(self, **kwargs):
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


cdef class Message:

	def __new__(self, **kwargs):
		if kwargs.get('sentinel') is not the_sentinel:
			raise InstantiationError
		self.ddjvu_message = NULL
	
	def __init(self):
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

	def __new__(self, Document document not None, int streamid, **kwargs):
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
	pass

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

class JobNotStarted(JobException):
	pass

class JobStarted(JobException):
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
