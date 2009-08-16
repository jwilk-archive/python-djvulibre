# encoding=UTF-8
# Copyright © 2007, 2008 Jakub Wilk <ubanus@users.sf.net>
#
# This package is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This package is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

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
        >>> document = context.new_document(FileUri('__nonexistent__'))
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
        >>> document = context.new_document(FileUri('t-gamma.djvu'))
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

        >>> file = document.files[0]
        >>> type(file) is File
        True
        >>> file.document is document
        True
        >>> file.get_info()
        >>> file.type
        'P'
        >>> file.n_page
        0
        >>> page = file.page
        >>> type(page) is Page
        True
        >>> page.document is document
        True
        >>> page.n
        0
        >>> file.size
        >>> file.id
        u't-gamma.djvu'
        >>> file.name
        u't-gamma.djvu'
        >>> file.title
        u't-gamma.djvu'

        >>> for line in document.files[0].dump.splitlines(): print repr(line) # doctest: +REPORT_NDIFF
        u'  FORM:DJVU [83] '
        u'    INFO [10]         DjVu 64x48, v24, 300 dpi, gamma=2.2'
        u'    Sjbz [53]         JB2 bilevel data'

        >>> page = document.pages[0]
        >>> type(page) is Page
        True
        >>> page.document is document
        True
        >>> page.get_info()
        >>> page.width
        64
        >>> page.height
        48
        >>> page.size
        (64, 48)
        >>> page.dpi
        300
        >>> page.rotation
        0
        >>> page.version
        24
        >>> file = page.file
        >>> type(file) is File
        True
        >>> file.id
        u't-gamma.djvu'
        
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
        IndexError: file number out of range
        >>> document.get_message(wait = False) is None
        True
        >>> context.get_message(wait = False) is None
        True
        
        >>> document.pages[-1]
        Traceback (most recent call last):
        ...
        IndexError: page number out of range
        >>> document.pages[1]
        Traceback (most recent call last):
        ...
        IndexError: page number out of range

        >>> document.get_message(wait = False) is None
        True
        >>> context.get_message(wait = False) is None
        True
        '''
    
    def test_save(self):
        r'''
        >>> context = Context()
        >>> document = context.new_document(FileUri('t-alpha.djvu'))
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
        '  FORM:DJVM [26871] '
        '    DIRM [84]         Document directory (bundled, 5 files 4 pages)'
        '    NAVM [193] '
        '    FORM:DJVU [5698] {p0001.djvu}'
        '      INFO [10]         DjVu 2550x3300, v24, 300 dpi, gamma=2.2'
        '      INCL [15]         Indirection chunk --> {shared_anno.iff}'
        '      Sjbz [4868]       JB2 bilevel data'
        '      TXTz [768]        Hidden text (text, etc.)'
        '    FORM:DJVI [203] {shared_anno.iff}'
        '      ANTz [191]        Page annotation (hyperlinks, etc.)'
        '    FORM:DJVU [2972] {p0002.djvu}'
        '      INFO [10]         DjVu 2550x3300, v24, 300 dpi, gamma=2.2'
        '      INCL [15]         Indirection chunk --> {shared_anno.iff}'
        '      Sjbz [1857]       JB2 bilevel data'
        '      FGbz [693]        JB2 colors data, v0, 216 colors'
        '      BG44 [87]         IW4 data #1, 97 slices, v1.2 (b&w), 213x275'
        '      TXTz [254]        Hidden text (text, etc.)'
        '    FORM:DJVU [3103] {p0003.djvu}'
        '      INFO [10]         DjVu 2550x3300, v24, 300 dpi, gamma=2.2'
        '      INCL [15]         Indirection chunk --> {shared_anno.iff}'
        '      Sjbz [1604]       JB2 bilevel data'
        '      FGbz [661]        JB2 colors data, v0, 216 colors'
        '      BG44 [208]        IW4 data #1, 97 slices, v1.2 (color), 213x275'
        '      TXTz [551]        Hidden text (text, etc.)'
        '    FORM:DJVU [14555] {p0004.djvu}'
        '      INFO [10]         DjVu 2550x3300, v24, 300 dpi, gamma=2.2'
        '      INCL [15]         Indirection chunk --> {shared_anno.iff}'
        '      Sjbz [2122]       JB2 bilevel data'
        '      FGbz [660]        JB2 colors data, v0, 216 colors'
        '      BG44 [2757]       IW4 data #1, 72 slices, v1.2 (color), 850x1100'
        '      BG44 [1840]       IW4 data #2, 11 slices'
        '      BG44 [2257]       IW4 data #3, 10 slices'
        '      BG44 [4334]       IW4 data #4, 10 slices'
        '      ANTz [111]        Page annotation (hyperlinks, etc.)'
        '      TXTz [361]        Hidden text (text, etc.)'
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
        '  FORM:DJVM [5983] '
        '    DIRM [53]         Document directory (bundled, 2 files 1 pages)'
        '    FORM:DJVU [5698] {p0001.djvu}'
        '      INFO [10]         DjVu 2550x3300, v24, 300 dpi, gamma=2.2'
        '      INCL [15]         Indirection chunk --> {shared_anno.iff}'
        '      Sjbz [4868]       JB2 bilevel data'
        '      TXTz [768]        Hidden text (text, etc.)'
        '    FORM:DJVI [203] {shared_anno.iff}'
        '      ANTz [191]        Page annotation (hyperlinks, etc.)'
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
        '  FORM:DJVM [277] '
        '    DIRM [64]         Document directory (indirect, 5 files 4 pages)'
        '      p0001.djvu -> p0001.djvu'
        '      shared_anno.iff -> shared_anno.iff'
        '      p0002.djvu -> p0002.djvu'
        '      p0003.djvu -> p0003.djvu'
        '      p0004.djvu -> p0004.djvu'
        '    NAVM [193] '
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
        >>> document = context.new_document(FileUri('t-alpha.djvu'))
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
        >>> for line in stdout.splitlines(): print repr(line.replace('  ', ' ')) # doctest: +REPORT_NDIFF
        ''
        ''
        ' 2 White background, colorful foreground red green blue cyan magenta yellow'
        ''
        ' red green blue cyan magenta yellow'
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

    >>> pf = PixelFormatRgbMask(0xff, 0xf00, 0x1f000, 0, 16)
    >>> pf
    djvu.decode.PixelFormatRgbMask(red_mask = 0x00ff, green_mask = 0x0f00, blue_mask = 0xf000, xor_value = 0x0000, bpp = 16)


    >>> pf = PixelFormatRgbMask(0xff000000, 0xff0000, 0xff00, 0xff, 32)
    >>> pf
    djvu.decode.PixelFormatRgbMask(red_mask = 0xff000000, green_mask = 0x00ff0000, blue_mask = 0x0000ff00, xor_value = 0x000000ff, bpp = 32)

    >>> pf = PixelFormatGrey()
    >>> pf
    djvu.decode.PixelFormatGrey(bpp = 8)

    >>> pf = PixelFormatPalette({})
    Traceback (most recent call last):
    ...
    KeyError: (0, 0, 0)
    >>> pf = PixelFormatPalette(dict(((i, j, k), i + 7*j + 37+k) for i in xrange(6) for j in xrange(6) for k in xrange(6)))
    >>> pf
    djvu.decode.PixelFormatPalette({(0, 0, 0): 0x25, (0, 0, 1): 0x26, (0, 0, 2): 0x27, (0, 0, 3): 0x28, (0, 0, 4): 0x29, (0, 0, 5): 0x2a, (0, 1, 0): 0x26, (0, 1, 1): 0x27, (0, 1, 2): 0x28, (0, 1, 3): 0x29, (0, 1, 4): 0x2a, (0, 1, 5): 0x2c, (0, 2, 0): 0x27, (0, 2, 1): 0x28, (0, 2, 2): 0x29, (0, 2, 3): 0x2a, (0, 2, 4): 0x2c, (0, 2, 5): 0x2d, (0, 3, 0): 0x28, (0, 3, 1): 0x29, (0, 3, 2): 0x2a, (0, 3, 3): 0x2c, (0, 3, 4): 0x2d, (0, 3, 5): 0x2e, (0, 4, 0): 0x29, (0, 4, 1): 0x2a, (0, 4, 2): 0x2c, (0, 4, 3): 0x2d, (0, 4, 4): 0x2e, (0, 4, 5): 0x2f, (0, 5, 0): 0x2a, (0, 5, 1): 0x2c, (0, 5, 2): 0x2d, (0, 5, 3): 0x2e, (0, 5, 4): 0x2f, (0, 5, 5): 0x30, (1, 0, 0): 0x26, (1, 0, 1): 0x27, (1, 0, 2): 0x28, (1, 0, 3): 0x29, (1, 0, 4): 0x2a, (1, 0, 5): 0x2b, (1, 1, 0): 0x27, (1, 1, 1): 0x28, (1, 1, 2): 0x29, (1, 1, 3): 0x2a, (1, 1, 4): 0x2b, (1, 1, 5): 0x2d, (1, 2, 0): 0x28, (1, 2, 1): 0x29, (1, 2, 2): 0x2a, (1, 2, 3): 0x2b, (1, 2, 4): 0x2d, (1, 2, 5): 0x2e, (1, 3, 0): 0x29, (1, 3, 1): 0x2a, (1, 3, 2): 0x2b, (1, 3, 3): 0x2d, (1, 3, 4): 0x2e, (1, 3, 5): 0x2f, (1, 4, 0): 0x2a, (1, 4, 1): 0x2b, (1, 4, 2): 0x2d, (1, 4, 3): 0x2e, (1, 4, 4): 0x2f, (1, 4, 5): 0x30, (1, 5, 0): 0x2b, (1, 5, 1): 0x2d, (1, 5, 2): 0x2e, (1, 5, 3): 0x2f, (1, 5, 4): 0x30, (1, 5, 5): 0x31, (2, 0, 0): 0x27, (2, 0, 1): 0x28, (2, 0, 2): 0x29, (2, 0, 3): 0x2a, (2, 0, 4): 0x2b, (2, 0, 5): 0x2c, (2, 1, 0): 0x28, (2, 1, 1): 0x29, (2, 1, 2): 0x2a, (2, 1, 3): 0x2b, (2, 1, 4): 0x2c, (2, 1, 5): 0x2e, (2, 2, 0): 0x29, (2, 2, 1): 0x2a, (2, 2, 2): 0x2b, (2, 2, 3): 0x2c, (2, 2, 4): 0x2e, (2, 2, 5): 0x2f, (2, 3, 0): 0x2a, (2, 3, 1): 0x2b, (2, 3, 2): 0x2c, (2, 3, 3): 0x2e, (2, 3, 4): 0x2f, (2, 3, 5): 0x30, (2, 4, 0): 0x2b, (2, 4, 1): 0x2c, (2, 4, 2): 0x2e, (2, 4, 3): 0x2f, (2, 4, 4): 0x30, (2, 4, 5): 0x31, (2, 5, 0): 0x2c, (2, 5, 1): 0x2e, (2, 5, 2): 0x2f, (2, 5, 3): 0x30, (2, 5, 4): 0x31, (2, 5, 5): 0x32, (3, 0, 0): 0x28, (3, 0, 1): 0x29, (3, 0, 2): 0x2a, (3, 0, 3): 0x2b, (3, 0, 4): 0x2c, (3, 0, 5): 0x2d, (3, 1, 0): 0x29, (3, 1, 1): 0x2a, (3, 1, 2): 0x2b, (3, 1, 3): 0x2c, (3, 1, 4): 0x2d, (3, 1, 5): 0x2f, (3, 2, 0): 0x2a, (3, 2, 1): 0x2b, (3, 2, 2): 0x2c, (3, 2, 3): 0x2d, (3, 2, 4): 0x2f, (3, 2, 5): 0x30, (3, 3, 0): 0x2b, (3, 3, 1): 0x2c, (3, 3, 2): 0x2d, (3, 3, 3): 0x2f, (3, 3, 4): 0x30, (3, 3, 5): 0x31, (3, 4, 0): 0x2c, (3, 4, 1): 0x2d, (3, 4, 2): 0x2f, (3, 4, 3): 0x30, (3, 4, 4): 0x31, (3, 4, 5): 0x32, (3, 5, 0): 0x2d, (3, 5, 1): 0x2f, (3, 5, 2): 0x30, (3, 5, 3): 0x31, (3, 5, 4): 0x32, (3, 5, 5): 0x33, (4, 0, 0): 0x29, (4, 0, 1): 0x2a, (4, 0, 2): 0x2b, (4, 0, 3): 0x2c, (4, 0, 4): 0x2d, (4, 0, 5): 0x2e, (4, 1, 0): 0x2a, (4, 1, 1): 0x2b, (4, 1, 2): 0x2c, (4, 1, 3): 0x2d, (4, 1, 4): 0x2e, (4, 1, 5): 0x30, (4, 2, 0): 0x2b, (4, 2, 1): 0x2c, (4, 2, 2): 0x2d, (4, 2, 3): 0x2e, (4, 2, 4): 0x30, (4, 2, 5): 0x31, (4, 3, 0): 0x2c, (4, 3, 1): 0x2d, (4, 3, 2): 0x2e, (4, 3, 3): 0x30, (4, 3, 4): 0x31, (4, 3, 5): 0x32, (4, 4, 0): 0x2d, (4, 4, 1): 0x2e, (4, 4, 2): 0x30, (4, 4, 3): 0x31, (4, 4, 4): 0x32, (4, 4, 5): 0x33, (4, 5, 0): 0x2e, (4, 5, 1): 0x30, (4, 5, 2): 0x31, (4, 5, 3): 0x32, (4, 5, 4): 0x33, (4, 5, 5): 0x34, (5, 0, 0): 0x2a, (5, 0, 1): 0x2b, (5, 0, 2): 0x2c, (5, 0, 3): 0x2d, (5, 0, 4): 0x2e, (5, 0, 5): 0x2f, (5, 1, 0): 0x2b, (5, 1, 1): 0x2c, (5, 1, 2): 0x2d, (5, 1, 3): 0x2e, (5, 1, 4): 0x2f, (5, 1, 5): 0x31, (5, 2, 0): 0x2c, (5, 2, 1): 0x2d, (5, 2, 2): 0x2e, (5, 2, 3): 0x2f, (5, 2, 4): 0x31, (5, 2, 5): 0x32, (5, 3, 0): 0x2d, (5, 3, 1): 0x2e, (5, 3, 2): 0x2f, (5, 3, 3): 0x31, (5, 3, 4): 0x32, (5, 3, 5): 0x33, (5, 4, 0): 0x2e, (5, 4, 1): 0x2f, (5, 4, 2): 0x31, (5, 4, 3): 0x32, (5, 4, 4): 0x33, (5, 4, 5): 0x34, (5, 5, 0): 0x2f, (5, 5, 1): 0x31, (5, 5, 2): 0x32, (5, 5, 3): 0x33, (5, 5, 4): 0x34, (5, 5, 5): 0x35}, bpp = 8)

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
        >>> document = context.new_document(FileUri('t-gamma.djvu'))
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
        >>> page_job.size
        (64, 48)
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
        ValueError: rotation must be equal to 0, 90, 180, or 270
        >>> page_job.rotation = 180
        >>> page_job.rotation, page_job.initial_rotation
        (180, 0)
        >>> del page_job.rotation
        >>> page_job.rotation, page_job.initial_rotation
        (0, 0)

        >>> page_job.render(RENDER_COLOR, (0, 0, -1, -1), (0, 0, 10, 10), PixelFormatRgb())
        Traceback (most recent call last):
        ...
        ValueError: page_rect width/height must be a positive integer

        >>> page_job.render(RENDER_COLOR, (0, 0, 10, 10), (0, 0, -1, -1), PixelFormatRgb())
        Traceback (most recent call last):
        ...
        ValueError: render_rect width/height must be a positive integer

        >>> page_job.render(RENDER_COLOR, (0, 0, 10, 10), (2, 2, 10, 10), PixelFormatRgb())
        Traceback (most recent call last):
        ...
        ValueError: render_rect must be inside page_rect

        >>> page_job.render(RENDER_COLOR, (0, 0, 10, 10), (0, 0, 10, 10), PixelFormatRgb(), -1)
        Traceback (most recent call last):
        ...
        ValueError: row_alignment must be a positive integer

        >>> page_job.render(RENDER_COLOR, (0, 0, 100000, 100000), (0, 0, 100000, 100000), PixelFormatRgb(), 8)
        Traceback (most recent call last):
        ...
        MemoryError: Unable to allocate 30000000000 bytes for an image buffer
        >>> page_job.render(RENDER_COLOR, (0, 0, 10, 10), (0, 0, 4, 4), PixelFormatGrey(), 1)
        '\xff\xff\xff\xff\xff\xff\xff\xef\xff\xff\xff\xa4\xff\xff\xff\xb8'
        '''

class ThumbnailTest:

    r'''
    >>> context = Context()
    >>> document = context.new_document(FileUri('t-gamma.djvu'))
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
    ValueError: need more than 2 values to unpack
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
    >>> document = context.new_document(FileUri('t-alpha.djvu'))
    >>> type(document) == Document
    True
    >>> message = document.get_message()
    >>> type(message) == DocInfoMessage
    True

    >>> anno = DocumentAnnotations(document, shared=False)
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
    Expression(((Symbol('metadata'), (Symbol('Author'), 'Jakub Wilk'), (Symbol('Creator'), 'LaTeX with hyperref package'), (Symbol('Producer'), 'pdfTeX-1.40.3\npdf2djvu 0.4.10 (DjVuLibre 3.5.21, poppler 0.6.4, GraphicsMagick++ 1.1.11)'), (Symbol('CreationDate'), '2008-03-02 23:56:13+01:00'), (Symbol('ModDate'), '2008-03-02 23:56:13+01:00')),))

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
    [u'2008-03-02 23:56:13+01:00', u'2008-03-02 23:56:13+01:00', u'Jakub Wilk', u'LaTeX with hyperref package', u'pdfTeX-1.40.3\npdf2djvu 0.4.10 (DjVuLibre 3.5.21, poppler 0.6.4, GraphicsMagick++ 1.1.11)']
    >>> sorted(metadata.itervalues()) == sorted(metadata.values())
    True
    >>> sorted(metadata.items())
    [(u'Author', u'Jakub Wilk'), (u'CreationDate', u'2008-03-02 23:56:13+01:00'), (u'Creator', u'LaTeX with hyperref package'), (u'ModDate', u'2008-03-02 23:56:13+01:00'), (u'Producer', u'pdfTeX-1.40.3\npdf2djvu 0.4.10 (DjVuLibre 3.5.21, poppler 0.6.4, GraphicsMagick++ 1.1.11)')]
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
    Expression((Symbol('bookmarks'), ('Black and white', '#p0001.djvu', ('Different font sizes', '#p0001.djvu'), ('Equation', '#p0001.djvu')), ('White background, colorful foreground', '#p0002.djvu'), ('Colorful solid background, black foreground', '#p0003.djvu'), ('Background with image, black foreground', '#p0004.djvu', ('Hyperlinks', '#p0004.djvu', ('Reference', '#p0004.djvu'), ('HTTP URI', '#p0004.djvu')), ('Photographic image', '#p0004.djvu'))))

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
    Expression(((Symbol('metadata'), (Symbol('Author'), 'Jakub Wilk'), (Symbol('Creator'), 'LaTeX with hyperref package'), (Symbol('Producer'), 'pdfTeX-1.40.3\npdf2djvu 0.4.10 (DjVuLibre 3.5.21, poppler 0.6.4, GraphicsMagick++ 1.1.11)'), (Symbol('CreationDate'), '2008-03-02 23:56:13+01:00'), (Symbol('ModDate'), '2008-03-02 23:56:13+01:00')), (Symbol('maparea'), '#p0001.djvu', '', (Symbol('rect'), 524, 2413, 33, 41), (Symbol('border'), Symbol('#ff0000'))), (Symbol('maparea'), 'http://jw209508.hopto.org/', '', (Symbol('rect'), 458, 2180, 675, 54), (Symbol('border'), Symbol('#00ffff')))))

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
    [Expression((Symbol('maparea'), '#p0001.djvu', '', (Symbol('rect'), 524, 2413, 33, 41), (Symbol('border'), Symbol('#ff0000')))), Expression((Symbol('maparea'), 'http://jw209508.hopto.org/', '', (Symbol('rect'), 458, 2180, 675, 54), (Symbol('border'), Symbol('#00ffff'))))]

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
    Expression((Symbol('page'), 0, 0, 2550, 3300, (Symbol('line'), 463, 2712, 2059, 2778, '4 Background with image, black foreground '), (Symbol('line'), 463, 2590, 933, 2643, '4.1 Hyperlinks '), (Symbol('line'), 463, 2509, 871, 2546, '4.1.1 Reference '), (Symbol('line'), 463, 2418, 547, 2450, '\xe2\x86\x921 '), (Symbol('line'), 463, 2287, 915, 2322, '4.1.2 HTTP URI '), (Symbol('line'), 462, 2184, 1124, 2229, 'http://jw209508.hopto.org/ '), (Symbol('line'), 463, 2039, 1199, 2092, '4.2 Photographic image '), (Symbol('line'), 1260, 375, 1281, 408, '4 ')))
    >>> text_s_detail[5] == text_s_detail[6] == text_s_detail[7] == text_s
    True
    >>> text_s
    Expression((Symbol('page'), 0, 0, 2550, 3300, (Symbol('line'), 463, 2712, 2059, 2778, (Symbol('word'), 463, 2727, 499, 2774, '4'), (Symbol('word'), 584, 2712, 1001, 2777, 'Background'), (Symbol('word'), 1031, 2727, 1185, 2777, 'with'), (Symbol('word'), 1217, 2712, 1437, 2777, 'image,'), (Symbol('word'), 1472, 2726, 1652, 2777, 'black'), (Symbol('word'), 1681, 2712, 2059, 2778, 'foreground')), (Symbol('line'), 463, 2590, 933, 2643, (Symbol('word'), 463, 2602, 541, 2640, '4.1'), (Symbol('word'), 616, 2590, 933, 2643, 'Hyperlinks')), (Symbol('line'), 463, 2509, 871, 2546, (Symbol('word'), 463, 2510, 572, 2543, '4.1.1'), (Symbol('word'), 634, 2509, 871, 2546, 'Reference')), (Symbol('line'), 463, 2418, 547, 2450, (Symbol('word'), 463, 2418, 547, 2450, '\xe2\x86\x921')), (Symbol('line'), 463, 2287, 915, 2322, (Symbol('word'), 463, 2288, 573, 2321, '4.1.2'), (Symbol('word'), 634, 2288, 789, 2322, 'HTTP'), (Symbol('word'), 812, 2287, 915, 2322, 'URI')), (Symbol('line'), 462, 2184, 1124, 2229, (Symbol('word'), 462, 2184, 1124, 2229, 'http://jw209508.hopto.org/')), (Symbol('line'), 463, 2039, 1199, 2092, (Symbol('word'), 463, 2051, 543, 2089, '4.2'), (Symbol('word'), 616, 2039, 1004, 2092, 'Photographic'), (Symbol('word'), 1034, 2039, 1199, 2091, 'image')), (Symbol('line'), 1260, 375, 1281, 408, (Symbol('word'), 1260, 375, 1281, 408, '4'))))
    >>> PageText(page, 'eggs')
    Traceback (most recent call last):
    ...
    TypeError: details must be a symbol or none
    >>> PageText(page, Symbol('eggs'))
    Traceback (most recent call last):
    ...
    ValueError: details must be equal to TEXT_DETAILS_PAGE, or TEXT_DETAILS_COLUMN, or TEXT_DETAILS_REGION, or TEXT_DETAILS_PARAGRAPH, or TEXT_DETAILS_LINE, or TEXT_DETAILS_WORD, or TEXT_DETAILS_CHARACTER or TEXT_DETAILS_ALL
    '''

if __name__ == '__main__':
    import os, sys
    os.chdir(sys.path[0])
    os.putenv('LC_ALL', 'C')
    del os, sys
    doctest.testmod(verbose = False)
    doctest.master.summarize(verbose = True)
    print
    unittest.main()
    print; print

# vim:ts=4 sw=4 et
