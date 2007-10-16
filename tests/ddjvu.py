from djvu.ddjvu import *
import unittest
import doctest

class ContextTest(unittest.TestCase):

	def test_cache(self):

		def set_cache_size(n):
			context.cache_size = n

		context = Context()
		self.assertEqual(context.cache_size, 10 << 20)
		for n in -100, 0, 1 << 32:
			self.assertRaises(ValueError, set_cache_size, n)
		self.assertRaises(ValueError, set_cache_size, 0)
		for n in 1, 100, 1 << 10, 1 << 20, (1 << 32) -1:
			set_cache_size(n)
			self.assertEqual(context.cache_size, n)
		context.clear_cache()


class DocumentTest:

	def test_instantiate(self):
		'''
		>>> Document()
		Traceback (most recent call last):
		...
		InstantiationError
		'''
	
	def test_nonexistent(self):
		'''
		>>> context = Context()
		>>> document = context.new_document(FileURI('__nonexistent__'))
		>>> document is None
		True
		>>> message = context.get_message()
		>>> type(message) == ErrorMessage
		True
		>>> message.message
		"[1-11711] Failed to open '__nonexistent__': No such file or directory."
		'''
	
	def test_new_document(self):
		'''
		>>> context = Context()
		>>> document = context.new_document(FileURI('ddjvu-g.djvu'))
		>>> type(document) == Document
		True
		>>> message = context.get_message()
		>>> type(message) == DocInfoMessage
		True
		>>> document.is_done
		True
		>>> document.is_error
		False
		>>> document.status == JobOK
		True
		>>> document.type == DOCUMENT_TYPE_SINGLE_PAGE
		True
		>>> len(document.pages)
		1
		>>> len(document.files)
		1

		>>> file_info = document.files[0].info
		>>> type(file_info) == FileInfo
		True
		>>> file_info.document is document
		True
		>>> file_info.type
		'P'
		>>> file_info.npage
		0
		>>> file_info.size
		>>> file_info.id
		u'ddjvu-g.djvu'
		>>> file_info.name
		u'ddjvu-g.djvu'
		>>> file_info.title
		u'ddjvu-g.djvu'

		>>> document.files[0].dump is None
		True

		>>> page_info = document.pages[0].info
		>>> type(page_info) == PageInfo
		True
		>>> page_info.document is document
		True
		>>> page_info.width
		64
		>>> page_info.height
		48
		>>> page_info.dpi
		300
		>>> page_info.rotation
		0
		>>> page_info.version
		24
		
		>>> document.pages[0].dump is None
		True

		>>> context.get_message(wait = False) is None
		True
		
		>>> document.files[-1].info
		Traceback (most recent call last):
		...
		JobFailed
		>>> message = context.get_message(wait = False)
		>>> type(message) == ErrorMessage
		True
		>>> message.message
		'Illegal file number'
		>>> context.get_message(wait = False) is None
		True
		
		>>> document.pages[-1].info
		Traceback (most recent call last):
		...
		ValueError
		>>> document.pages[1].info
		Traceback (most recent call last):
		...
		JobFailed
		>>> message = context.get_message()
		>>> message.message
		'[1-13001] Page number is too big.'
		>>> type(message) == ErrorMessage
		True

		>>> foo_page = document.pages[u'foo']
		>>> isinstance(foo_page, Page)
		True
		>>> foo_page.n
		Traceback (most recent call last):
		...
		NotImplementedError
		>>> foo_page.id
		u'foo'
		>>> foo_page.dump
		Traceback (most recent call last):
		...
		NotImplementedError
		>>> foo_page.info
		Traceback (most recent call last):
		...
		NotImplementedError

		>>> context.get_message(wait = False) is None
		True
		'''

class PageJobTest:

	def test_instantiation():
		'''
		>>> PageJob()
		Traceback (most recent call last):
		...
		InstantiationError
		'''
	
	def test_decode():
		'''
		>>> context = Context()
		>>> document = context.new_document(FileURI('ddjvu-g.djvu'))
		>>> message = context.get_message()
		>>> type(message) == DocInfoMessage
		True
		>>> page_job = document.pages[0].decode()
		>>> message = context.get_message()
		>>> type(message) == ChunkMessage
		True
		>>> type(page_job) == PageJob
		True
		>>> page_job.is_done
		True
		>>> page_job.is_error
		False
		>>> page_job.status == JobOK
		True
		>>> page_job.width
		64
		>>> page_job.height
		48
		>>> page_job.resolution
		300
		>>> page_job.gamma
		2.2000000000000002
		>>> page_job.version
		24
		>>> page_job.type == PAGE_TYPE_BITONAL
		True
		>>> (page_job.rotation, page_job.initial_rotation)
		(0, 0)
		>>> page_job.rotation = 100
		Traceback (most recent call last):
		...
		ValueError
		>>> page_job.rotation = 180
		>>> (page_job.rotation, page_job.initial_rotation)
		(180, 0)
		>>> del page_job.rotation
		>>> (page_job.rotation, page_job.initial_rotation)
		(0, 0)
		'''

class JobTest:
	'''
	>>> Job()
	Traceback (most recent call last):
	...
	InstantiationError
	'''

class MessageTest:
	'''
	>>> Message()
	Traceback (most recent call last):
	...
	InstantiationError
	'''

class StreamTest:
	'''
	>>> Stream(None, 42)
	Traceback (most recent call last):
	...
	TypeError: Argument 'document' has incorrect type (expected ddjvu.Document, got NoneType)
	
	>>> context = Context()
	>>> document = context.new_document('dummy://dummy.djvu')
	>>> message = context.get_message()
	>>> type(message) == NewStreamMessage
	True
	>>> message.name
	'dummy.djvu'
	>>> message.uri
	'dummy://dummy.djvu'
	>>> type(message.stream) == Stream
	True
	
	>>> try:
	...   message.stream.write(file('ddjvu-g.djvu').read())
	... finally:
	...   message.stream.close()
	>>> message.stream.write('foo')
	Traceback (most recent call last):
	...
	IOError: I/O operation on closed file
	
	>>> message = context.get_message()
	>>> type(message) == DocInfoMessage
	True
	'''

if __name__ == '__main__':
	import os, sys
	os.chdir(sys.path[0])
	del os, sys
	doctest.testmod(verbose = False)
	doctest.master.summarize(verbose = True)
	print
	unittest.main()
	print; print

# vim:ts=4 sw=4 noet
