from djvu.ddjvu import *
import unittest
import doctest

class ContextTest(unittest.TestCase):

	THE_CONTEXT = Context()

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
		>>> document.type == DOCUMENT_TYPE_SINGLE_PAGE
		True
		>>> document.npages
		1
		>>> document.nfiles
		1

		>>> file_info = document.get_file_info(0)
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

		>>> page_info = document.get_page_info(0)
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

		>>> message = context.get_message(wait = False)
		>>> message is None
		True
		'''

class PageTest:
	'''
	>>> Page()
	Traceback (most recent call last):
	...
	InstantiationError
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
