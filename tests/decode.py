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

		>>> context.get_message(wait = False) is None
		True
		'''
	
	def test_save(self):
		r'''
		>>> class MyContext(Context):
		...   def handle_message(self, message): pass
		>>> context = MyContext()
		>>> document = context.new_document(FileURI('test-p.djvu'))
		>>> message = context.get_message()
		>>> type(message) == DocInfoMessage
		True
		>>> document.is_done
		True
		>>> document.is_error
		False
		>>> document.status == JobOK
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
		>>> type(job) == Job
		True
		>>> job.is_done, job.is_error
		(True, False)
		>>> stdout, stderr = Popen(['djvudump', tmp.name], stdout = PIPE, stderr = PIPE).communicate()
		>>> stderr
		''
		>>> for line in stdout.splitlines(): print repr(line)
		...
		'  FORM:DJVM [8393] '
		'    DIRM [83]         Document directory (bundled, 5 files 4 pages)'
		'    NAVM [123] '
		'    FORM:DJVU [528] {p0001.djvu}'
		'      INFO [10]         DjVu 612x792, v24, 72 dpi, gamma=2.2'
		'      INCL [15]         Indirection chunk --> {shared_anno.iff}'
		'      Sjbz [274]        JB2 bilevel data'
		'      TXTz [192]        Hidden text (text, etc.)'
		'    FORM:DJVI [179] {shared_anno.iff}'
		'      ANTz [167]        Page annotation (hyperlinks, etc.)'
		'    FORM:DJVU [1738] {p0002.djvu}'
		'      INFO [10]         DjVu 612x792, v24, 72 dpi, gamma=2.2'
		'      INCL [15]         Indirection chunk --> {shared_anno.iff}'
		'      Sjbz [637]        JB2 bilevel data'
		'      FGbz [730]        JB2 colors data'
		'      BG44 [19]         IW4 data #1, 97 slices, v1.2 (b&w), 51x66'
		'      TXTz [272]        Hidden text (text, etc.)'
		'    FORM:DJVU [1300] {p0003.djvu}'
		'      INFO [10]         DjVu 612x792, v24, 72 dpi, gamma=2.2'
		'      INCL [15]         Indirection chunk --> {shared_anno.iff}'
		'      Sjbz [308]        JB2 bilevel data'
		'      FGbz [660]        JB2 colors data'
		'      BG44 [43]         IW4 data #1, 97 slices, v1.2 (color), 51x66'
		'      TXTz [210]        Hidden text (text, etc.)'
		'    FORM:DJVU [4379] {p0004.djvu}'
		'      INFO [10]         DjVu 612x792, v24, 72 dpi, gamma=2.2'
		'      INCL [15]         Indirection chunk --> {shared_anno.iff}'
		'      Sjbz [900]        JB2 bilevel data'
		'      FGbz [661]        JB2 colors data'
		'      BG44 [433]        IW4 data #1, 72 slices, v1.2 (color), 204x264'
		'      BG44 [328]        IW4 data #2, 11 slices'
		'      BG44 [443]        IW4 data #3, 10 slices'
		'      BG44 [865]        IW4 data #4, 10 slices'
		'      ANTz [93]         Page annotation (hyperlinks, etc.)'
		'      TXTz [541]        Hidden text (text, etc.)'
		>>> del tmp

		>>> tmp = NamedTemporaryFile()
		>>> job = document.save(tmp.file, pages=(1,))
		>>> type(job) == Job
		True
		>>> job.is_done, job.is_error
		(True, False)
		>>> stdout, stderr = Popen(['djvudump', tmp.name], stdout = PIPE, stderr = PIPE).communicate()
		>>> stderr
		''
		>>> for line in stdout.splitlines(): print repr(line)
		...
		'  FORM:DJVM [789] '
		'    DIRM [54]         Document directory (bundled, 2 files 1 pages)'
		'    FORM:DJVU [528] {p0001.djvu}'
		'      INFO [10]         DjVu 612x792, v24, 72 dpi, gamma=2.2'
		'      INCL [15]         Indirection chunk --> {shared_anno.iff}'
		'      Sjbz [274]        JB2 bilevel data'
		'      TXTz [192]        Hidden text (text, etc.)'
		'    FORM:DJVI [179] {shared_anno.iff}'
		'      ANTz [167]        Page annotation (hyperlinks, etc.)'
		>>> del tmp
		
		>>> tmpdir = mkdtemp()
		>>> tmpfname = path_join(tmpdir, 'index.djvu')
		>>> job = document.save(indirect = tmpfname)
		>>> type(job) == Job
		True
		>>> job.is_done, job.is_error
		(True, False)
		>>> stdout, stderr = Popen(['djvudump', tmpfname], stdout = PIPE, stderr = PIPE).communicate()
		>>> stderr
		''
		>>> for line in stdout.splitlines(): print repr(line)
		...
		'  FORM:DJVM [207] '
		'    DIRM [63]         Document directory (indirect, 5 files 4 pages)'
		'      p0001.djvu -> p0001.djvu'
		'      shared_anno.iff -> shared_anno.iff'
		'      p0002.djvu -> p0002.djvu'
		'      p0003.djvu -> p0003.djvu'
		'      p0004.djvu -> p0004.djvu'
		'    NAVM [123] '
		>>> rmtree(tmpdir)

		>>> tmpdir = mkdtemp()
		>>> tmpfname = path_join(tmpdir, 'index.djvu')
		>>> job = document.save(indirect = tmpfname, pages = (1,))
		>>> type(job) == Job
		True
		>>> job.is_done, job.is_error
		(True, False)
		>>> stdout, stderr = Popen(['djvudump', tmpfname], stdout = PIPE, stderr = PIPE).communicate()
		>>> stderr
		''
		>>> for line in stdout.splitlines(): print repr(line)
		...
		'  FORM:DJVM [58] '
		'    DIRM [46]         Document directory (indirect, 2 files 1 pages)'
		'      p0001.djvu -> p0001.djvu'
		'      shared_anno.iff -> shared_anno.iff'
		>>> rmtree(tmpdir)
		'''

	def test_export_ps(self):
		r'''
		>>> class MyContext(Context):
		...   def handle_message(self, message): pass
		>>> context = MyContext()
		>>> document = context.new_document(FileURI('test-p.djvu'))
		>>> message = context.get_message()
		>>> type(message) == DocInfoMessage
		True
		>>> document.is_done
		True
		>>> document.is_error
		False
		>>> document.status == JobOK
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
		>>> type(job) == Job
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
		>>> job = document.export_ps(tmp.file, pages = (2, 3), text = True)
		>>> type(job) == Job
		True
		>>> job.is_done, job.is_error
		(True, False)
		>>> stdout, stderr = Popen(['ps2ascii', tmp.name], stdout = PIPE, stderr = PIPE).communicate()
		>>> stderr
		''
		>>> for line in stdout.splitlines(): print repr(line)
		''
		''
		' (White background, colorful foreground.)  2  Color samples  red green blue cyan magenta yellow red'
		''
		' green  blue  cyan  magenta yellow'
		''
		' 2\x0c'
		''
		' (Colorful solild background, black foreground.)  2.1  Even  more  colors  Yes, looks odd.'
		''
		' 3'
		>>> del tmp
		'''


class PixelFormatTest:

	'''
	>>> PixelFormat()
	Traceback (most recent call last):
	...
	InstantiationError

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
	ValueError
	>>> pf = PixelFormatPalette([0] * 300)
	Traceback (most recent call last):
	...
	ValueError
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
		InstantiationError
		'''
	
	def test_decode():
		r'''
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
		>>> page_job.rotation, page_job.initial_rotation
		(0, 0)
		>>> page_job.rotation = 100
		Traceback (most recent call last):
		...
		ValueError
		>>> page_job.rotation = 180
		>>> page_job.rotation, page_job.initial_rotation
		(180, 0)
		>>> del page_job.rotation
		>>> page_job.rotation, page_job.initial_rotation
		(0, 0)

		>>> page_job.render(RENDER_COLOR, (0, 0, 10, 10), (0, 0, 100000, 100000), PixelFormatRgb(), 8)
		Traceback (most recent call last):
		...
		MemoryError: Unable to alocate 30000000000 bytes for an image buffer
		>>> page_job.render(RENDER_COLOR, (0, 0, 10, 10), (0, 0, 4, 4), PixelFormatGrey(), 1)
		'\xff\xff\xff\xff\xff\xff\xff\xef\xff\xff\xff\xa4\xff\xff\xff\xb8'
		'''

class ThumbnailTest:

	r'''
	>>> class MyContext(Context):
	...   def handle_message(self, message): pass

	>>> context = MyContext()
	>>> document = context.new_document(FileURI('test-g.djvu'))
	>>> message = context.get_message()
	>>> type(message) == DocInfoMessage
	True
	>>> thumbnail = document.pages[0].thumbnail
	>>> thumbnail.status == JobOK
	True
	>>> thumbnail.calculate() == JobOK
	True
	>>> message = context.get_message()
	>>> type(message) == ThumbnailMessage
	True
	>>> message.n
	0
	>>> thumbnail.render((5, 5), PixelFormatGrey(), dry_run = True)
	((5, 3), None)
	>>> (w, h), pixels = thumbnail.render((5, 5), PixelFormatGrey())
	>>> w, h
	(5, 3)
	>>> pixels[:15]
	'\xff\xeb\xa7\xf2\xff\xff\xbf\x86\xbe\xff\xff\xe7\xd6\xe7\xff'
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
	>>> af(x for x in (0, 0, 10, 10))
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
	>>> af.reverse(x for x in (17, 42, 42, 100))
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
	TypeError: Argument 'document' has incorrect type (expected djvu.decode.Document, got NoneType)
	
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

class SexprTest:
	r'''
	>>> context = Context()
	>>> document = context.new_document(FileURI('test-p.djvu'))
	>>> type(document) == Document
	True
	>>> message = context.get_message()
	>>> type(message) == DocInfoMessage
	True

	>>> anno = DocumentAnnotations(document, compat = False)
	>>> type(anno) == DocumentAnnotations
	True
	>>> anno.sexpr
	Expression(())

	>>> anno = document.annotations
	>>> type(anno) == DocumentAnnotations
	True
	>>> anno.background_color
	>>> anno.horizontal_align
	>>> anno.vertical_align
	>>> anno.mode
	>>> anno.zoom
	>>> anno.sexpr
	Expression(((Symbol('metadata'), (Symbol('ModDate'), '2007-12-07 18:11:10+01:00'), (Symbol('CreationDate'), '2007-12-07 18:11:10+01:00'), (Symbol('Producer'), 'pdfTeX-1.40.3\npdf2djvu 0.4.5 (DjVuLibre , poppler 3.5.20)'), (Symbol('Creator'), 'LaTeX with hyperref package'), (Symbol('Author'), 'Jakub Wilk')),))

	>>> metadata = anno.metadata
	>>> type(metadata) == Metadata
	True
	>>> len(metadata)
	5
	>>> sorted(metadata.keys())
	[u'Author', u'CreationDate', u'Creator', u'ModDate', u'Producer']
	>>> k = 'ModDate'
	>>> k in metadata
	True
	>>> metadata[k]
	u'2007-12-07 18:11:10+01:00'
	>>> metadata['foo']
	Traceback (most recent call last):
	...
	KeyError: 'foo'

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
	>>> outline.sexpr
	Expression((Symbol('bookmarks'), ('First equation', '#1'), ('Color samples', '#2', ('Even more colors', '#3')), ('Second equation', '#4', ('Vari\xc3\xa9t\xc3\xa9s', '#4', ('HTTP URI', '#4'), ('Different font sizes', '#4'), ('Photo', '#4')))))

	>>> page = document.pages[3]
	>>> anno = page.annotations
	>>> type(anno) == PageAnnotations
	True
	>>> anno.background_color
	>>> anno.horizontal_align
	>>> anno.vertical_align
	>>> anno.mode
	>>> anno.zoom
	>>> anno.sexpr
	Expression(((Symbol('metadata'), (Symbol('ModDate'), '2007-12-07 18:11:10+01:00'), (Symbol('CreationDate'), '2007-12-07 18:11:10+01:00'), (Symbol('Producer'), 'pdfTeX-1.40.3\npdf2djvu 0.4.5 (DjVuLibre , poppler 3.5.20)'), (Symbol('Creator'), 'LaTeX with hyperref package'), (Symbol('Author'), 'Jakub Wilk')), (Symbol('maparea'), '#1', '', (Symbol('rect'), 255, 610, 8, 13), (Symbol('border'), Symbol('#ff0000'))), (Symbol('maparea'), 'http://jw209508.hopto.org/', '', (Symbol('rect'), 110, 504, 162, 13), (Symbol('border'), Symbol('#ff0000')))))

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
	[Expression((Symbol('maparea'), '#1', '', (Symbol('rect'), 255, 610, 8, 13), (Symbol('border'), Symbol('#ff0000')))), Expression((Symbol('maparea'), 'http://jw209508.hopto.org/', '', (Symbol('rect'), 110, 504, 162, 13), (Symbol('border'), Symbol('#ff0000'))))]

	>>> text = page.text
	>>> type(text) == PageText
	True
	>>> text.sexpr
	Expression((Symbol('page'), 0, 0, 612, 792, (Symbol('line'), 110, 652, 277, 672, '3 Second equation '), (Symbol('line'), 110, 625, 309, 639, '(Image background, black foreground.) '), (Symbol('line'), 128, 611, 311, 625, 'In addition to equation (1) consider '), (Symbol('line'), 281, 587, 328, 599, '2+1=3 '), (Symbol('line'), 484, 585, 498, 599, '(2) '), (Symbol('line'), 110, 553, 204, 567, '3.1 Vari\xc2\xb4et\xc2\xb4es '), (Symbol('line'), 110, 531, 220, 542, '3.1.1 HTTP URI '), (Symbol('line'), 110, 506, 270, 520, 'http://jw209508.hopto.org/ '), (Symbol('line'), 110, 477, 262, 488, '3.1.2 Di\xef\xac\x80erent font sizes '), (Symbol('line'), 110, 436, 498, 460, 'Poo qoo Poo qoo Poo qoo Poo qoo Poo qoo Poo qoo Poo qoo Poo qoo '), (Symbol('line'), 110, 405, 280, 434, 'Poo qoo Poo qoo '), (Symbol('line'), 110, 361, 186, 372, '3.1.3 Photo '), (Symbol('line'), 302, 90, 307, 101, '4 ')))
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
