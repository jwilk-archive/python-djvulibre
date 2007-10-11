# Copyright (c) 2007 Jakub Wilk <ubanus@users.sf.net>

cdef extern from 'Python.h':
	int PyString_AsStringAndSize(object, char**, int*) except -1
	object PyString_FromStringAndSize(char *s, int len)


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

cdef class Document:

	def __new__(self, **kwargs):
		if kwargs.get('sentinel') is not the_sentinel:
			raise InstantiationError
		self.ddjvu_document = NULL

	property status:
		def __get__(self):
			return ddjvu_document_decoding_status(self.ddjvu_document)

	property is_error:
		def __get__(self):
			return bool(ddjvu_document_decoding_error(self.ddjvu_document))
	
	property is_done:
		def __get__(self):
			return bool(ddjvu_document_decoding_done(self.ddjvu_document))

	property type:
		def __get__(self):
			return ddjvu_document_get_type(self.ddjvu_document)

	property npages:
		def __get__(self):
			return ddjvu_document_get_pagenum(self.ddjvu_document)

	property nfiles:
		def __get__(self):
			return ddjvu_document_get_filenum(self.ddjvu_document)

	def get_file_info(self, int nfile):
		cdef ddjvu_status_t status
		cdef FileInfo file_info
		file_info = FileInfo(self, sentinel = the_sentinel)
		status = ddjvu_document_get_fileinfo(self.ddjvu_document, nfile, &file_info.ddjvu_fileinfo)
		if status != <int> DDJVU_JOB_OK:
			raise JobError(status)
		return file_info

	def get_page_info(self, int npage):
		cdef ddjvu_status_t status
		cdef PageInfo page_info
		page_info = PageInfo(self, sentinel = the_sentinel)
		status = ddjvu_document_get_pageinfo(self.ddjvu_document, npage, &page_info.ddjvu_pageinfo)
		if status != <int> DDJVU_JOB_OK:
			raise JobError(status)
		return page_info

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


cdef class Page:
	
	def __new__(self, **kwargs):
		if kwargs.get('sentinel') is not the_sentinel:
			raise InstantiationError
		self.ddjvu_page = NULL

cdef Page Page_from_c(ddjvu_page_t* ddjvu_page):
	cdef Page result
	if ddjvu_page == NULL:
		result = None
	else:
		result = Page(sentinel = the_sentinel)
		result.ddjvu_page = ddjvu_page
	return result

JOB_NOTSTARTED = DDJVU_JOB_NOTSTARTED
JOB_STARTED = DDJVU_JOB_STARTED
JOB_OK = DDJVU_JOB_OK
JOB_FAILED = DDJVU_JOB_FAILED
JOB_STOPPED = DDJVU_JOB_STOPPED

cdef class Job:

	def __new__(self, **kwargs):
		if kwargs.get('sentinel') is not the_sentinel:
			raise InstantiationError
		self.ddjvu_job = NULL

	property status:
		def __get__(self):
			return ddjvu_job_status(self.ddjvu_job)

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
		self._page = Page_from_c(self.ddjvu_message.m_any.page)
		self._job = Job_from_c(self.ddjvu_message.m_any.job)
	
	property context:
		def __get__(self):
			return self._context

	property document:
		def __get__(self):
			return self._document

	property page:
		def __get__(self):
			return self._page

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

class JobError(Exception):
	pass

# vim:ts=4 sw=4 noet
