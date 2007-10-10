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

	def test_new_nonexistent_document(self):
		context = Context()
		document = context.new_document(FileURI('__nonexistent__'))
		self.assertEqual(document, None)
		message = context.get_message()
		self.assertEqual(type(message), ErrorMessage)
		self.assertEqual(message.message, "[1-11711] Failed to open '__nonexistent__': No such file or directory.")
	
	def test_new_document(self):
		context = Context()
		document = context.new_document(FileURI('ddjvu-g.djvu'))
		self.assertEqual(type(document), Document)
		message = context.get_message()
		self.assertEqual(type(message), DocInfoMessage)
		message = context.get_message(wait = False)
		self.assertEqual(message, None)

class DocumentTest:
	'''
	>>> Document()
	Traceback (most recent call last):
	...
	InstantiationError
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
