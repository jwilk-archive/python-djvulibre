from djvu.decode import *
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
		>>> document = context.new_document(FileURI('test-g.djvu'))
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
		u'test-g.djvu'
		>>> file_info.name
		u'test-g.djvu'
		>>> file_info.title
		u'test-g.djvu'

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

#		>>> document.pages[1].info
#		Traceback (most recent call last):
#		...
#		JobFailed
#		>>> message = context.get_message()
#		>>> message.message
#		'[1-13001] Page number is too big.'
#		>>> type(message) == ErrorMessage
#		True

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

class PixelFormatTest:

	'''
	>>> PixelFormat()
	Traceback (most recent call last):
	...
	InstantiationError

	>>> PixelFormatTrueColor()
	Traceback (most recent call last):
	...
	InstantiationError

	>>> pf = PixelFormatBgr24()
	>>> pf
	decode.PixelFormatBgr24()
	>>> pf.bpp
	24

	>>> pf = PixelFormatRgb24()
	>>> pf
	decode.PixelFormatRgb24()
	>>> pf.bpp
	24

	>>> PixelFormatRgbMask()
	Traceback (most recent call last):
	...
	InstantiationError
	>>> pf = PixelFormatRgbMask16(57005, 48815, 1717, 4242)
	>>> pf
	decode.PixelFormatRgbMask16(0xdead, 0xbeaf, 0x06b5, 0x1092)
	>>> pf.bpp
	16

	>>> pf = PixelFormatRgbMask32(424242, 3735928559, 171717, 373737)
	>>> pf
	decode.PixelFormatRgbMask32(0x00067932, 0xdeadbeef, 0x00029ec5, 0x0005b3e9)
	>>> pf.bpp
	32

	>>> PixelFormatGrey()
	Traceback (most recent call last):
	...
	InstantiationError
	>>> pf = PixelFormatGrey8()
	>>> pf
	decode.PixelFormatGrey8()
	>>> pf.bpp
	8

	>>> PixelFormatPalette()
	Traceback (most recent call last):
	...
	InstantiationError
	>>> pf = PixelFormatPalette8([])
	Traceback (most recent call last):
	...
	ValueError
	>>> pf = PixelFormatPalette8([0] * 300)
	Traceback (most recent call last):
	...
	ValueError
	>>> pf = PixelFormatPalette8((x * x * 107) % 217 for x in xrange(216))
	>>> pf
	decode.PixelFormatPalette8([0x00, 0x6b, 0xd3, 0x5f, 0xc1, 0x47, 0xa3, 0x23, 0x79, 0xcc, 0x43, 0x90, 0x01, 0x48, 0x8c, 0xcd, 0x32, 0x6d, 0xa5, 0x01, 0x33, 0x62, 0x8e, 0xb7, 0x04, 0x27, 0x47, 0x64, 0x7e, 0x95, 0xa9, 0xba, 0xc8, 0xd3, 0x02, 0x07, 0x09, 0x08, 0x04, 0xd6, 0xcc, 0xbf, 0xaf, 0x9c, 0x86, 0x6d, 0x51, 0x32, 0x10, 0xc4, 0x9c, 0x71, 0x43, 0x12, 0xb7, 0x80, 0x46, 0x09, 0xa2, 0x5f, 0x19, 0xa9, 0x5d, 0x0e, 0x95, 0x40, 0xc1, 0x66, 0x08, 0x80, 0x1c, 0x8e, 0x24, 0x90, 0x20, 0x86, 0x10, 0x70, 0xcd, 0x4e, 0xa5, 0x20, 0x71, 0xbf, 0x31, 0x79, 0xbe, 0x27, 0x66, 0xa2, 0x02, 0x38, 0x6b, 0x9b, 0xc8, 0x19, 0x40, 0x64, 0x85, 0xa3, 0xbe, 0xd6, 0x12, 0x24, 0x33, 0x3f, 0x48, 0x4e, 0x51, 0x51, 0x4e, 0x48, 0x3f, 0x33, 0x24, 0x12, 0xd6, 0xbe, 0xa3, 0x85, 0x64, 0x40, 0x19, 0xc8, 0x9b, 0x6b, 0x38, 0x02, 0xa2, 0x66, 0x27, 0xbe, 0x79, 0x31, 0xbf, 0x71, 0x20, 0xa5, 0x4e, 0xcd, 0x70, 0x10, 0x86, 0x20, 0x90, 0x24, 0x8e, 0x1c, 0x80, 0x08, 0x66, 0xc1, 0x40, 0x95, 0x0e, 0x5d, 0xa9, 0x19, 0x5f, 0xa2, 0x09, 0x46, 0x80, 0xb7, 0x12, 0x43, 0x71, 0x9c, 0xc4, 0x10, 0x32, 0x51, 0x6d, 0x86, 0x9c, 0xaf, 0xbf, 0xcc, 0xd6, 0x04, 0x08, 0x09, 0x07, 0x02, 0xd3, 0xc8, 0xba, 0xa9, 0x95, 0x7e, 0x64, 0x47, 0x27, 0x04, 0xb7, 0x8e, 0x62, 0x33, 0x01, 0xa5, 0x6d, 0x32, 0xcd, 0x8c, 0x48, 0x01, 0x90, 0x43, 0xcc, 0x79, 0x23, 0xa3, 0x47, 0xc1, 0x5f, 0xd3])
	>>> pf.bpp
	8

	>>> pf = PixelFormatPackedBits()
	Traceback (most recent call last):
	...
	InstantiationError
	>>> pf = PixelFormatMsbToLsb()
	>>> pf
	decode.PixelFormatMsbToLsb()
	>>> pf.bpp
	1
	
	>>> pf = PixelFormatLsbToMsb()
	>>> pf
	decode.PixelFormatLsbToMsb()
	>>> pf.bpp
	1
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
		>>> class MyContext(Context):
		...   def handle_message(self, message): pass

		>>> context = MyContext()
		>>> document = context.new_document(FileURI('test-g.djvu'))
		>>> message = context.get_message()
		>>> type(message) == DocInfoMessage
		True
		>>> page_job = document.pages[0].decode()
		>>> page_job.is_done
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

		>>> page_job.render(RENDER_COLOR, (0, 0, 10, 10), (0, 0, 100000, 100000), PixelFormatRgb24(), 8)
		Traceback (most recent call last):
		...
		MemoryError: Unable to alocate 30000000000 bytes for an image buffer
		>>> page_job.render(RENDER_COLOR, (0, 0, 10, 10), (0, 0, 4, 4), PixelFormatGrey8(), 1)
		'\\xff\\xff\\xff\\xff\\xff\\xff\\xff\\xef\\xff\\xff\\xff\\xa4\\xff\\xff\\xff\\xb8'
		'''

class JobTest:
	'''
	>>> Job()
	Traceback (most recent call last):
	...
	InstantiationError
	'''

class AffineTransformTest:
	'''
	>>> AffineTransform((1, 2), (3, 4, 5))
	Traceback (most recent call last):
	...
	ValueError: unpack sequence of wrong size
	>>> af = AffineTransform((0, 0, 10, 10), (17, 42, 42, 100))
	>>> type(af) == AffineTransform
	True
	>>> af((0, 0))
	(17, 42)
	>>> af((0, 10))
	(17, 142)
	>>> af((10, 0))
	(59, 42)
	>>> af((10, 10))
	(59, 142)
	>>> af((0, 0, 10, 10))
	(17, 42, 42, 100)
	>>> af.apply((123, 456)) == af((123, 456))
	True
	>>> af.apply((12, 34, 56, 78)) == af((12, 34, 56, 78))
	True
	>>> af.reverse((17, 42))
	(0, 0)
	>>> af.reverse((17, 142))
	(0, 10)
	>>> af.reverse((59, 42))
	(10, 0)
	>>> af.reverse((59, 142))
	(10, 10)
	>>> af.reverse((17, 42, 42, 100))
	(0, 0, 10, 10)
	>>> af.reverse(af((234, 567))) == (234, 567)
	True
	>>> af.reverse(af((23, 45, 67, 78))) == (23, 45, 67, 78)
	True
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
	TypeError: Argument 'document' has incorrect type (expected decode.Document, got NoneType)
	
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
	...   message.stream.write(file('test-g.djvu').read())
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
