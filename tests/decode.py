from djvu.decode import *
from djvu.sexpr import *
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
		TypeError: cannot create 'djvu.decode.Document' instances
		'''
	
	def test_nonexistent(self):
		'''
		>>> context = Context()
		>>> document = context.new_document(FileURI('__nonexistent__'))
		Traceback (most recent call last):
		...
		JobFailed
		>>> message = context.get_message()
		>>> type(message) == ErrorMessage
		True
		>>> message.message
		"[1-11711] Failed to open '__nonexistent__': No such file or directory."
		'''
	
	def test_new_document(self):
		'''
		>>> context = Context()
		>>> document = context.new_document(FileURI('t-gamma.djvu'))
		>>> type(document) == Document
		True
		>>> message = document.get_message()
		>>> type(message) == DocInfoMessage
		True
		>>> document.decoding_done
		True
		>>> document.decoding_error
		False
		>>> document.decoding_status == JobOK
		True
		>>> document.type == DOCUMENT_TYPE_SINGLE_PAGE
		True
		>>> len(document.pages)
		1
		>>> len(document.files)
		1

		>>> decoding_job = document.decoding_job
		>>> decoding_job.is_done, decoding_job.is_error
		(True, False)
		>>> decoding_job.status == JobOK
		True

		>>> file_info = document.files[0].get_info()
		>>> type(file_info) == FileInfo
		True
		>>> file_info.document is document
		True
		>>> file_info.type
		'P'
		>>> file_info.n_page
		0
		>>> file_info.size
		>>> file_info.id
		u't-gamma.djvu'
		>>> file_info.name
		u't-gamma.djvu'
		>>> file_info.title
		u't-gamma.djvu'

		>>> for line in document.files[0].dump.splitlines(): print repr(line) # doctest: +REPORT_NDIFF
		u'  FORM:DJVU [83] '
		u'    INFO [10]         DjVu 64x48, v24, 300 dpi, gamma=2.2'
		u'    Sjbz [53]         JB2 bilevel data'

		>>> page_info = document.pages[0].get_info()
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
		
		>>> for line in document.pages[0].dump.splitlines(): print repr(line) # doctest: +REPORT_NDIFF
		u'  FORM:DJVU [83] '
		u'    INFO [10]         DjVu 64x48, v24, 300 dpi, gamma=2.2'
		u'    Sjbz [53]         JB2 bilevel data'

		>>> document.get_message(wait = False) is None
		True
		>>> context.get_message(wait = False) is None
		True
		
		>>> document.files[-1].get_info()
		Traceback (most recent call last):
		...
		JobFailed
		>>> message = document.get_message(wait = False)
		>>> type(message) == ErrorMessage
		True
		>>> message.message
		'Illegal file number'
		>>> document.get_message(wait = False) is None
		True
		>>> context.get_message(wait = False) is None
		True
		
		>>> document.pages[-1].get_info()
		Traceback (most recent call last):
		...
		IndexError: page number out of range

#		>>> document.pages[1].get_info()
#		Traceback (most recent call last):
#		...
#		JobFailed
#		>>> message = context.get_message()
#		>>> message.message
#		'[1-13001] Page number is too big.'
#		>>> type(message) == ErrorMessage
#		True

		>>> document.get_message(wait = False) is None
		True
		>>> context.get_message(wait = False) is None
		True
		'''
	
	def test_save(self):
		r'''
		>>> context = Context()
		>>> document = context.new_document(FileURI('t-alpha.djvu'))
		>>> message = document.get_message()
		>>> type(message) == DocInfoMessage
		True
		>>> document.decoding_done
		True
		>>> document.decoding_error
		False
		>>> document.decoding_status == JobOK
		True
		>>> document.type == DOCUMENT_TYPE_BUNDLED
		True
		>>> len(document.pages)
		4
		>>> len(document.files)
		5
			
		>>> from tempfile import NamedTemporaryFile, mkdtemp
		>>> from shutil import rmtree
		>>> from os.path import join as path_join
		>>> from subprocess import Popen, PIPE

		>>> tmp = NamedTemporaryFile()
		>>> job = document.save(tmp.file)
		>>> type(job) == SaveJob
		True
		>>> job.is_done, job.is_error
		(True, False)
		>>> stdout, stderr = Popen(['djvudump', tmp.name], stdout = PIPE, stderr = PIPE).communicate()
		>>> stderr
		''
		>>> for line in stdout.splitlines(): print repr(line) # doctest: +REPORT_NDIFF
		...
		'  FORM:DJVM [26888] '
		'    DIRM [82]         Document directory (bundled, 5 files 4 pages)'
		'    NAVM [173] '
		'    FORM:DJVU [5669] {p0001.djvu}'
		'      INFO [10]         DjVu 2550x3300, v24, 300 dpi, gamma=2.2'
		'      INCL [15]         Indirection chunk --> {shared_anno.iff}'
		'      Sjbz [4868]       JB2 bilevel data'
		'      TXTz [739]        Hidden text (text, etc.)'
		'    FORM:DJVI [204] {shared_anno.iff}'
		'      ANTz [192]        Page annotation (hyperlinks, etc.)'
		'    FORM:DJVU [3095] {p0002.djvu}'
		'      INFO [10]         DjVu 2550x3300, v24, 300 dpi, gamma=2.2'
		'      INCL [15]         Indirection chunk --> {shared_anno.iff}'
		'      Sjbz [1963]       JB2 bilevel data'
		'      FGbz [715]        JB2 colors data, v0, 216 colors'
		'      BG44 [87]         IW4 data #1, 97 slices, v1.2 (b&w), 213x275'
		'      TXTz [249]        Hidden text (text, etc.)'
		'    FORM:DJVU [3079] {p0003.djvu}'
		'      INFO [10]         DjVu 2550x3300, v24, 300 dpi, gamma=2.2'
		'      INCL [15]         Indirection chunk --> {shared_anno.iff}'
		'      Sjbz [1604]       JB2 bilevel data'
		'      FGbz [661]        JB2 colors data, v0, 216 colors'
		'      BG44 [208]        IW4 data #1, 97 slices, v1.2 (color), 213x275'
		'      TXTz [527]        Hidden text (text, etc.)'
		'    FORM:DJVU [14522] {p0004.djvu}'
		'      INFO [10]         DjVu 2550x3300, v24, 300 dpi, gamma=2.2'
		'      INCL [15]         Indirection chunk --> {shared_anno.iff}'
		'      Sjbz [2122]       JB2 bilevel data'
		'      FGbz [660]        JB2 colors data, v0, 216 colors'
		'      BG44 [2757]       IW4 data #1, 72 slices, v1.2 (color), 850x1100'
		'      BG44 [1840]       IW4 data #2, 11 slices'
		'      BG44 [2257]       IW4 data #3, 10 slices'
		'      BG44 [4334]       IW4 data #4, 10 slices'
		'      ANTz [101]        Page annotation (hyperlinks, etc.)'
		'      TXTz [338]        Hidden text (text, etc.)'
		>>> del tmp

		>>> tmp = NamedTemporaryFile()
		>>> job = document.save(tmp.file, pages=(0,))
		>>> type(job) == SaveJob
		True
		>>> job.is_done, job.is_error
		(True, False)
		>>> stdout, stderr = Popen(['djvudump', tmp.name], stdout = PIPE, stderr = PIPE).communicate()
		>>> stderr
		''
		>>> for line in stdout.splitlines(): print repr(line) # doctest: +REPORT_NDIFF
		...
		'  FORM:DJVM [5956] '
		'    DIRM [53]         Document directory (bundled, 2 files 1 pages)'
		'    FORM:DJVU [5669] {p0001.djvu}'
		'      INFO [10]         DjVu 2550x3300, v24, 300 dpi, gamma=2.2'
		'      INCL [15]         Indirection chunk --> {shared_anno.iff}'
		'      Sjbz [4868]       JB2 bilevel data'
		'      TXTz [739]        Hidden text (text, etc.)'
		'    FORM:DJVI [204] {shared_anno.iff}'
		'      ANTz [192]        Page annotation (hyperlinks, etc.)'
		>>> del tmp
		
		>>> tmpdir = mkdtemp()
		>>> tmpfname = path_join(tmpdir, 'index.djvu')
		>>> job = document.save(indirect = tmpfname)
		>>> type(job) == SaveJob
		True
		>>> job.is_done, job.is_error
		(True, False)
		>>> stdout, stderr = Popen(['djvudump', tmpfname], stdout = PIPE, stderr = PIPE).communicate()
		>>> stderr
		''
		>>> for line in stdout.splitlines(): print repr(line) # doctest: +REPORT_NDIFF
		...
		'  FORM:DJVM [255] '
		'    DIRM [62]         Document directory (indirect, 5 files 4 pages)'
		'      p0001.djvu -> p0001.djvu'
		'      shared_anno.iff -> shared_anno.iff'
		'      p0002.djvu -> p0002.djvu'
		'      p0003.djvu -> p0003.djvu'
		'      p0004.djvu -> p0004.djvu'
		'    NAVM [173] '
		>>> rmtree(tmpdir)

		>>> tmpdir = mkdtemp()
		>>> tmpfname = path_join(tmpdir, 'index.djvu')
		>>> job = document.save(indirect = tmpfname, pages = (0,))
		>>> type(job) == SaveJob
		True
		>>> job.is_done, job.is_error
		(True, False)
		>>> stdout, stderr = Popen(['djvudump', tmpfname], stdout = PIPE, stderr = PIPE).communicate()
		>>> stderr
		''
		>>> for line in stdout.splitlines(): print repr(line) # doctest: +REPORT_NDIFF
		...
		'  FORM:DJVM [57] '
		'    DIRM [45]         Document directory (indirect, 2 files 1 pages)'
		'      p0001.djvu -> p0001.djvu'
		'      shared_anno.iff -> shared_anno.iff'
		>>> rmtree(tmpdir)
		'''

	def test_export_ps(self):
		r'''
		>>> import sys
		>>> context = Context()
		>>> document = context.new_document(FileURI('t-alpha.djvu'))
		>>> message = document.get_message()
		>>> type(message) == DocInfoMessage
		True
		>>> document.decoding_done
		True
		>>> document.decoding_error
		False
		>>> document.decoding_status == JobOK
		True
		>>> document.type == DOCUMENT_TYPE_BUNDLED
		True
		>>> len(document.pages)
		4
		>>> len(document.files)
		5
			
		>>> from tempfile import NamedTemporaryFile
		>>> from subprocess import Popen, PIPE
		>>> from pprint import pprint

		>>> tmp = NamedTemporaryFile()
		>>> job = document.export_ps(tmp.file)
		>>> type(job) == SaveJob
		True
		>>> job.is_done, job.is_error
		(True, False)
		>>> stdout, stderr = Popen(['ps2ascii', tmp.name], stdout = PIPE, stderr = PIPE).communicate()
		>>> stderr
		''
		>>> stdout
		'\x0c\x0c\x0c'
		>>> del tmp

		>>> tmp = NamedTemporaryFile()
		>>> job = document.export_ps(tmp.file, pages = (1,), text = True)
		>>> type(job) == SaveJob
		True
		>>> job.is_done, job.is_error
		(True, False)
		>>> stdout, stderr = Popen(['ps2ascii', tmp.name], stdout = PIPE, stderr = PIPE).communicate()
		>>> stderr
		''
		>>> for line in stdout.splitlines(): print repr(line) # doctest: +REPORT_NDIFF
		''
		''
		' 2  White background, colorful foreground  red green blue cyan magenta yellow red  green blue cyan magenta yellow'
		''
		' 2'
		>>> del tmp
		'''

class PixelFormatTest:

	'''
	>>> PixelFormat()
	Traceback (most recent call last):
	...
	TypeError: cannot create 'djvu.decode.PixelFormat' instances

	>>> pf = PixelFormatRgb()
	>>> pf
	djvu.decode.PixelFormatRgb(byte_order = 'RGB', bpp = 24)
	>>> pf = PixelFormatRgb('RGB')
	>>> pf
	djvu.decode.PixelFormatRgb(byte_order = 'RGB', bpp = 24)
	>>> pf = PixelFormatRgb('BGR')
	>>> pf
	djvu.decode.PixelFormatRgb(byte_order = 'BGR', bpp = 24)

	>>> pf = PixelFormatRgbMask(57005, 48815, 1717, 4242, 16)
	>>> pf
	djvu.decode.PixelFormatRgbMask(red_mask = 0xdead, green_mask = 0xbeaf, blue_mask = 0x06b5, xor_value = 0x1092, bpp = 16)

	>>> pf = PixelFormatRgbMask(424242, 3735928559, 171717, 373737, 32)
	>>> pf
	djvu.decode.PixelFormatRgbMask(red_mask = 0x00067932, green_mask = 0xdeadbeef, blue_mask = 0x00029ec5, xor_value = 0x0005b3e9, bpp = 32)

	>>> pf = PixelFormatGrey()
	>>> pf
	djvu.decode.PixelFormatGrey(bpp = 8)

	>>> pf = PixelFormatPalette([])
	Traceback (most recent call last):
	...
	ValueError: `palette` must be a sequence of 216 integers
	>>> pf = PixelFormatPalette([0] * 300)
	Traceback (most recent call last):
	...
	ValueError: `palette` must be a sequence of 216 integers
	>>> pf = PixelFormatPalette((x * x * 107) % 217 for x in xrange(216))
	>>> pf
	djvu.decode.PixelFormatPalette([0x00, 0x6b, 0xd3, 0x5f, 0xc1, 0x47, 0xa3, 0x23, 0x79, 0xcc, 0x43, 0x90, 0x01, 0x48, 0x8c, 0xcd, 0x32, 0x6d, 0xa5, 0x01, 0x33, 0x62, 0x8e, 0xb7, 0x04, 0x27, 0x47, 0x64, 0x7e, 0x95, 0xa9, 0xba, 0xc8, 0xd3, 0x02, 0x07, 0x09, 0x08, 0x04, 0xd6, 0xcc, 0xbf, 0xaf, 0x9c, 0x86, 0x6d, 0x51, 0x32, 0x10, 0xc4, 0x9c, 0x71, 0x43, 0x12, 0xb7, 0x80, 0x46, 0x09, 0xa2, 0x5f, 0x19, 0xa9, 0x5d, 0x0e, 0x95, 0x40, 0xc1, 0x66, 0x08, 0x80, 0x1c, 0x8e, 0x24, 0x90, 0x20, 0x86, 0x10, 0x70, 0xcd, 0x4e, 0xa5, 0x20, 0x71, 0xbf, 0x31, 0x79, 0xbe, 0x27, 0x66, 0xa2, 0x02, 0x38, 0x6b, 0x9b, 0xc8, 0x19, 0x40, 0x64, 0x85, 0xa3, 0xbe, 0xd6, 0x12, 0x24, 0x33, 0x3f, 0x48, 0x4e, 0x51, 0x51, 0x4e, 0x48, 0x3f, 0x33, 0x24, 0x12, 0xd6, 0xbe, 0xa3, 0x85, 0x64, 0x40, 0x19, 0xc8, 0x9b, 0x6b, 0x38, 0x02, 0xa2, 0x66, 0x27, 0xbe, 0x79, 0x31, 0xbf, 0x71, 0x20, 0xa5, 0x4e, 0xcd, 0x70, 0x10, 0x86, 0x20, 0x90, 0x24, 0x8e, 0x1c, 0x80, 0x08, 0x66, 0xc1, 0x40, 0x95, 0x0e, 0x5d, 0xa9, 0x19, 0x5f, 0xa2, 0x09, 0x46, 0x80, 0xb7, 0x12, 0x43, 0x71, 0x9c, 0xc4, 0x10, 0x32, 0x51, 0x6d, 0x86, 0x9c, 0xaf, 0xbf, 0xcc, 0xd6, 0x04, 0x08, 0x09, 0x07, 0x02, 0xd3, 0xc8, 0xba, 0xa9, 0x95, 0x7e, 0x64, 0x47, 0x27, 0x04, 0xb7, 0x8e, 0x62, 0x33, 0x01, 0xa5, 0x6d, 0x32, 0xcd, 0x8c, 0x48, 0x01, 0x90, 0x43, 0xcc, 0x79, 0x23, 0xa3, 0x47, 0xc1, 0x5f, 0xd3], bpp = 8)

	>>> pf = PixelFormatPackedBits('<')
	>>> pf
	djvu.decode.PixelFormatPackedBits('<')
	>>> pf.bpp
	1
	
	>>> pf = PixelFormatPackedBits('>')
	>>> pf
	djvu.decode.PixelFormatPackedBits('>')
	>>> pf.bpp
	1
	'''

class PageJobTest:

	def test_instantiation():
		'''
		>>> PageJob()
		Traceback (most recent call last):
		...
		TypeError: cannot create 'djvu.decode.PageJob' instances
		'''
	
	def test_decode():
		r'''
		>>> context = Context()
		>>> document = context.new_document(FileURI('t-gamma.djvu'))
		>>> message = document.get_message()
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
		>>> page_job.dpi
		300
		>>> page_job.gamma
		2.2000000000000002
		>>> page_job.version
		24
		>>> page_job.type == PAGE_TYPE_BITONAL
		True
		>>> page_job.rotation, page_job.initial_rotation
		(0, 0)
		>>> page_job.rotation = 100
		Traceback (most recent call last):
		...
		ValueError: `rotation` must be equal to 0, 90, 180, or 270
		>>> page_job.rotation = 180
		>>> page_job.rotation, page_job.initial_rotation
		(180, 0)
		>>> del page_job.rotation
		>>> page_job.rotation, page_job.initial_rotation
		(0, 0)

		>>> page_job.render(RENDER_COLOR, (0, 0, -1, -1), (0, 0, 10, 10), PixelFormatRgb())
		Traceback (most recent call last):
		...
		ValueError: page_rect
		>>> page_job.render(RENDER_COLOR, (0, 0, 10, 10), (0, 0, -1, -1), PixelFormatRgb())
		Traceback (most recent call last):
		...
		ValueError: render_rect
		>>> page_job.render(RENDER_COLOR, (0, 0, 10, 10), (0, 0, 10, 10), PixelFormatRgb(), -1)
		Traceback (most recent call last):
		...
		ValueError: row_alignment

		>>> page_job.render(RENDER_COLOR, (0, 0, 10, 10), (0, 0, 100000, 100000), PixelFormatRgb(), 8)
		Traceback (most recent call last):
		...
		MemoryError: Unable to alocate 30000000000 bytes for an image buffer
		>>> page_job.render(RENDER_COLOR, (0, 0, 10, 10), (0, 0, 4, 4), PixelFormatGrey(), 1)
		'\xff\xff\xff\xff\xff\xff\xff\xef\xff\xff\xff\xa4\xff\xff\xff\xb8'
		'''

class ThumbnailTest:

	r'''
	>>> context = Context()
	>>> document = context.new_document(FileURI('t-gamma.djvu'))
	>>> message = document.get_message()
	>>> type(message) == DocInfoMessage
	True
	>>> thumbnail = document.pages[0].thumbnail
	>>> thumbnail.status == JobOK
	True
	>>> thumbnail.calculate() == JobOK
	True
	>>> message = document.get_message()
	>>> type(message) == ThumbnailMessage
	True
	>>> message.thumbnail.page.n
	0
	>>> thumbnail.render((5, 5), PixelFormatGrey(), dry_run = True)
	((5, 3, 5), None)
	>>> (w, h, r), pixels = thumbnail.render((5, 5), PixelFormatGrey())
	>>> w, h, r
	(5, 3, 5)
	>>> pixels[:15]
	'\xff\xeb\xa7\xf2\xff\xff\xbf\x86\xbe\xff\xff\xe7\xd6\xe7\xff'
	'''

class JobTest:
	'''
	>>> Job()
	Traceback (most recent call last):
	...
	TypeError: cannot create 'djvu.decode.Job' instances
	
	>>> DocumentDecodingJob()
	Traceback (most recent call last):
	...
	TypeError: cannot create 'djvu.decode.DocumentDecodingJob' instances
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
	>>> af(x for x in (0, 0, 10, 10))
	(17, 42, 42, 100)
	>>> af.apply((123, 456)) == af((123, 456))
	True
	>>> af.apply((12, 34, 56, 78)) == af((12, 34, 56, 78))
	True
	>>> af.inverse((17, 42))
	(0, 0)
	>>> af.inverse((17, 142))
	(0, 10)
	>>> af.inverse((59, 42))
	(10, 0)
	>>> af.inverse((59, 142))
	(10, 10)
	>>> af.inverse((17, 42, 42, 100))
	(0, 0, 10, 10)
	>>> af.inverse(x for x in (17, 42, 42, 100))
	(0, 0, 10, 10)
	>>> af.inverse(af((234, 567))) == (234, 567)
	True
	>>> af.inverse(af((23, 45, 67, 78))) == (23, 45, 67, 78)
	True
	'''

class MessageTest:
	'''
	>>> Message()
	Traceback (most recent call last):
	...
	TypeError: cannot create 'djvu.decode.Message' instances
	'''

class StreamTest:
	'''
	>>> Stream(None, 42)
	Traceback (most recent call last):
	...
	TypeError: Argument 'document' has incorrect type (expected djvu.decode.Document, got NoneType)
	
	>>> context = Context()
	>>> document = context.new_document('dummy://dummy.djvu')
	>>> message = document.get_message()
	>>> type(message) == NewStreamMessage
	True
	>>> message.name
	'dummy.djvu'
	>>> message.uri
	'dummy://dummy.djvu'
	>>> type(message.stream) == Stream
	True

	>>> document.outline.sexpr
	Traceback (most recent call last):
	...
	NotAvailable
	>>> document.annotations.sexpr
	Traceback (most recent call last):
	...
	NotAvailable
	>>> document.pages[0].text.sexpr
	Traceback (most recent call last):
	...
	NotAvailable
	>>> document.pages[0].annotations.sexpr
	Traceback (most recent call last):
	...
	NotAvailable
	
	>>> try:
	...   message.stream.write(file('t-gamma.djvu').read())
	... finally:
	...   message.stream.close()
	>>> message.stream.write('eggs')
	Traceback (most recent call last):
	...
	IOError: I/O operation on closed file
	
	>>> message = document.get_message()
	>>> type(message) == DocInfoMessage
	True

	>>> outline = document.outline
	>>> outline.wait()
	>>> outline.sexpr
	Expression(())
	>>> anno = document.annotations
	>>> anno.wait()
	>>> anno.sexpr
	Expression(())
	>>> text = document.pages[0].text
	>>> text.wait()
	>>> text.sexpr
	Expression(())
	>>> anno = document.pages[0].annotations
	>>> anno.wait()
	>>> anno.sexpr
	Expression(())
	'''

class SexprTest:
	r'''
	>>> context = Context()
	>>> document = context.new_document(FileURI('t-alpha.djvu'))
	>>> type(document) == Document
	True
	>>> message = document.get_message()
	>>> type(message) == DocInfoMessage
	True

	>>> anno = DocumentAnnotations(document, compat = False)
	>>> type(anno) == DocumentAnnotations
	True
	>>> anno.wait()
	>>> anno.sexpr
	Expression(())

	>>> anno = document.annotations
	>>> type(anno) == DocumentAnnotations
	True
	>>> anno.wait()
	>>> anno.background_color
	>>> anno.horizontal_align
	>>> anno.vertical_align
	>>> anno.mode
	>>> anno.zoom
	>>> anno.sexpr
	Expression(((Symbol('metadata'), (Symbol('ModDate'), '2008-03-02 23:56:13+01:00'), (Symbol('CreationDate'), '2008-03-02 23:56:13+01:00'), (Symbol('Producer'), 'pdfTeX-1.40.3\npdf2djvu 0.4.9 (DjVuLibre 3.5.21, poppler 0.6.4, GraphicsMagick++ 1.1.10)'), (Symbol('Creator'), 'LaTeX with hyperref package'), (Symbol('Author'), 'Jakub Wilk')),))

	>>> metadata = anno.metadata
	>>> type(metadata) == Metadata
	True
	>>> len(metadata)
	5
	>>> sorted(metadata.keys())
	[u'Author', u'CreationDate', u'Creator', u'ModDate', u'Producer']
	>>> sorted(metadata.iterkeys()) == sorted(metadata.keys())
	True
	>>> sorted(metadata.values())
	[u'2008-03-02 23:56:13+01:00', u'2008-03-02 23:56:13+01:00', u'Jakub Wilk', u'LaTeX with hyperref package', u'pdfTeX-1.40.3\npdf2djvu 0.4.9 (DjVuLibre 3.5.21, poppler 0.6.4, GraphicsMagick++ 1.1.10)']
	>>> sorted(metadata.itervalues()) == sorted(metadata.values())
	True
	>>> sorted(metadata.items())
	[(u'Author', u'Jakub Wilk'), (u'CreationDate', u'2008-03-02 23:56:13+01:00'), (u'Creator', u'LaTeX with hyperref package'), (u'ModDate', u'2008-03-02 23:56:13+01:00'), (u'Producer', u'pdfTeX-1.40.3\npdf2djvu 0.4.9 (DjVuLibre 3.5.21, poppler 0.6.4, GraphicsMagick++ 1.1.10)')]
	>>> sorted(metadata.iteritems()) == sorted(metadata.items())
	True
	>>> k = 'ModDate'
	>>> k in metadata
	True
	>>> metadata[k]
	u'2008-03-02 23:56:13+01:00'
	>>> metadata['eggs']
	Traceback (most recent call last):
	...
	KeyError: 'eggs'

	>>> hyperlinks = anno.hyperlinks
	>>> type(hyperlinks) == Hyperlinks
	True
	>>> len(hyperlinks)
	0
	>>> list(hyperlinks)
	[]

	>>> outline = document.outline
	>>> type(outline) == DocumentOutline
	True
	>>> outline.wait()
	>>> outline.sexpr
	Expression((Symbol('bookmarks'), ('Black and white', '#1', ('Different font sizes', '#1'), ('Equation', '#1')), ('White background, colorful foreground', '#2'), ('Colorful solid background, black foreground', '#3'), ('Background with image, black foreground', '#4', ('Hyperlinks', '#4', ('Reference', '#4'), ('HTTP URI', '#4')), ('Photographic image', '#4'))))

	>>> page = document.pages[3]
	>>> anno = page.annotations
	>>> type(anno) == PageAnnotations
	True
	>>> anno.wait()
	>>> anno.background_color
	>>> anno.horizontal_align
	>>> anno.vertical_align
	>>> anno.mode
	>>> anno.zoom
	>>> anno.sexpr
	Expression(((Symbol('metadata'), (Symbol('ModDate'), '2008-03-02 23:56:13+01:00'), (Symbol('CreationDate'), '2008-03-02 23:56:13+01:00'), (Symbol('Producer'), 'pdfTeX-1.40.3\npdf2djvu 0.4.9 (DjVuLibre 3.5.21, poppler 0.6.4, GraphicsMagick++ 1.1.10)'), (Symbol('Creator'), 'LaTeX with hyperref package'), (Symbol('Author'), 'Jakub Wilk')), (Symbol('maparea'), '#1', '', (Symbol('rect'), 524, 2413, 33, 41), (Symbol('border'), Symbol('#ff0000'))), (Symbol('maparea'), 'http://jw209508.hopto.org/', '', (Symbol('rect'), 458, 2180, 675, 54), (Symbol('border'), Symbol('#00ffff')))))

	>>> page_metadata = anno.metadata
	>>> type(page_metadata) == Metadata
	True
	>>> page_metadata.keys() == metadata.keys()
	True
	>>> [page_metadata[k] == metadata[k] for k in metadata]
	[True, True, True, True, True]

	>>> hyperlinks = anno.hyperlinks
	>>> type(hyperlinks) == Hyperlinks
	True
	>>> len(hyperlinks)
	2
	>>> list(hyperlinks)
	[Expression((Symbol('maparea'), '#1', '', (Symbol('rect'), 524, 2413, 33, 41), (Symbol('border'), Symbol('#ff0000')))), Expression((Symbol('maparea'), 'http://jw209508.hopto.org/', '', (Symbol('rect'), 458, 2180, 675, 54), (Symbol('border'), Symbol('#00ffff'))))]

	>>> text = page.text
	>>> type(text) == PageText
	True
	>>> text.wait()
	>>> text_s = text.sexpr
	>>> text_s_detail = [PageText(page, details).sexpr for details in (TEXT_DETAILS_PAGE, TEXT_DETAILS_COLUMN, TEXT_DETAILS_REGION, TEXT_DETAILS_PARAGRAPH, TEXT_DETAILS_LINE, TEXT_DETAILS_WORD, TEXT_DETAILS_CHARACTER, TEXT_DETAILS_ALL)]
	>>> text_s_detail[0] == text_s_detail[1] == text_s_detail[2] == text_s_detail[3]
	True
	>>> text_s_detail[0]
	Expression((Symbol('page'), 0, 0, 2550, 3300, '4 Background with image, black foreground \n4.1 Hyperlinks \n4.1.1 Reference \n\xe2\x86\x921 \n4.1.2 HTTP URI \nhttp://jw209508.hopto.org/ \n4.2 Photographic image \n4 \n'))
	>>> text_s_detail[4]
	Expression((Symbol('page'), 0, 0, 2550, 3300, (Symbol('line'), 461, 2712, 2061, 2798, '4 Background with image, black foreground '), (Symbol('line'), 461, 2590, 936, 2661, '4.1 Hyperlinks '), (Symbol('line'), 461, 2509, 872, 2559, '4.1.1 Reference '), (Symbol('line'), 461, 2418, 551, 2467, '\xe2\x86\x921 '), (Symbol('line'), 461, 2287, 916, 2337, '4.1.2 HTTP URI '), (Symbol('line'), 461, 2184, 1127, 2244, 'http://jw209508.hopto.org/ '), (Symbol('line'), 461, 2039, 1202, 2110, '4.2 Photographic image '), (Symbol('line'), 1259, 375, 1283, 424, '4 ')))
	>>> text_s_detail[5] == text_s_detail[6] == text_s_detail[7] == text_s
	True
	>>> text_s
	Expression((Symbol('page'), 0, 0, 2550, 3300, (Symbol('line'), 461, 2712, 2061, 2798, (Symbol('word'), 461, 2727, 501, 2798, '4'), (Symbol('word'), 582, 2712, 1003, 2798, 'Background'), (Symbol('word'), 1030, 2727, 1186, 2798, 'with'), (Symbol('word'), 1214, 2712, 1442, 2798, 'image,'), (Symbol('word'), 1470, 2726, 1652, 2798, 'black'), (Symbol('word'), 1679, 2712, 2061, 2798, 'foreground')), (Symbol('line'), 461, 2590, 936, 2661, (Symbol('word'), 461, 2602, 547, 2661, '4.1'), (Symbol('word'), 615, 2590, 936, 2661, 'Hyperlinks')), (Symbol('line'), 461, 2509, 872, 2559, (Symbol('word'), 461, 2510, 577, 2559, '4.1.1'), (Symbol('word'), 633, 2509, 872, 2559, 'Reference')), (Symbol('line'), 461, 2418, 551, 2467, (Symbol('word'), 461, 2418, 551, 2467, '\xe2\x86\x921')), (Symbol('line'), 461, 2287, 916, 2337, (Symbol('word'), 461, 2288, 577, 2337, '4.1.2'), (Symbol('word'), 633, 2288, 792, 2337, 'HTTP'), (Symbol('word'), 811, 2287, 916, 2337, 'URI')), (Symbol('line'), 461, 2184, 1127, 2244, (Symbol('word'), 461, 2184, 1127, 2244, 'http://jw209508.hopto.org/')), (Symbol('line'), 461, 2039, 1202, 2110, (Symbol('word'), 461, 2051, 547, 2110, '4.2'), (Symbol('word'), 615, 2039, 1007, 2110, 'Photographic'), (Symbol('word'), 1031, 2039, 1202, 2110, 'image')), (Symbol('line'), 1259, 375, 1283, 424, (Symbol('word'), 1259, 375, 1283, 424, '4'))))
	>>> PageText(page, 'eggs')
	Traceback (most recent call last):
	...
	TypeError: `details` must be a symbol or none
	>>> PageText(page, Symbol('eggs'))
	Traceback (most recent call last):
	...
	ValueError: `details` must be equal to `TEXT_DETAILS_PAGE`, or `TEXT_DETAILS_COLUMN`, or `TEXT_DETAILS_REGION`, or `TEXT_DETAILS_PARAGRAPH`, or `TEXT_DETAILS_LINE`, or `TEXT_DETAILS_WORD`, or `TEXT_DETAILS_CHARACTER` or `TEXT_DETAILS_ALL`
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
