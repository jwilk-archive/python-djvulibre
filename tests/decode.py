# encoding=UTF-8
# Copyright © 2007, 2008, 2009, 2010 Jakub Wilk <jwilk@jwilk.net>
#
# This package is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This package is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

from nose.tools import *

from djvu.decode import *
from djvu.sexpr import *

import os
import tempfile
import subprocess

images = os.path.join(os.path.dirname(__file__), 'images', '')

def create_djvu(commands='', sexpr=''):
    if sexpr:
        commands += '\nset-ant\n%s\n.\n' % sexpr
    file = tempfile.NamedTemporaryFile()
    file = open('test.djvu', 'w')
    file.seek(0)
    file.write('AT&TFORM\0\0\0"DJVUINFO\0\0\0\n\0\1\0\1\x18\0,\1\x16\1Sjbz\0\0\0\x04\xbcs\x1b\xd7')
    file.flush()
    djvused = subprocess.Popen(['djvused', '-s', file.name], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE) #, env={})
    djvused.stdin.write(commands)
    djvused.stdin.close()
    assert_equal(djvused.wait(), 0)
    assert_equal(djvused.stdout.read(), '')
    assert_equal(djvused.stderr.read(), '')
    return file

def test_context_cache():

    def set_cache_size(n):
        context.cache_size = n

    context = Context()
    assert_equal(context.cache_size, 10 << 20)
    for n in -100, 0, 1 << 32:
        assert_raises(ValueError, set_cache_size, n)
    assert_raises(ValueError, set_cache_size, 0)
    for n in 1, 100, 1 << 10, 1 << 20, (1 << 32) -1:
        set_cache_size(n)
        assert_equal(context.cache_size, n)
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
        >>> document = context.new_document(FileUri(images + 'test1.djvu'))
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
        u'test1.djvu'
        >>> file.name
        u'test1.djvu'
        >>> file.title
        u'test1.djvu'

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
        u'test1.djvu'

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
        >>> document = context.new_document(FileUri(images + 'test0.djvu'))
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
        6
        >>> len(document.files)
        7

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
        >>> tmp.flush()
        >>> stdout, stderr = Popen(['djvudump', tmp.name], stdout=PIPE, stderr=PIPE, env={}).communicate()
        >>> stderr
        ''
        >>> for line in stdout.splitlines(): print repr(line) # doctest: +REPORT_NDIFF,+ELLIPSIS
        '  FORM:DJVM [...] '
        '    DIRM [...] ... Document directory (bundled, 7 files 6 pages)'
        '    NAVM [...] '
        '    FORM:DJVI [...] {shared_anno.iff}...'
        '      ANTz [...] ... Page annotation (hyperlinks, etc.)'
        '    FORM:DJVU [...] {p0001.djvu}...'
        '      INFO [...] ... DjVu 2550x3300, v24, 300 dpi, gamma=2.2'
        '      INCL [...] ... Indirection chunk --> {shared_anno.iff}'
        '      Sjbz [...] ... JB2 bilevel data'
        '      TXTz [...] ... Hidden text (text, etc.)'
        '    FORM:DJVU [...] {p0002.djvu}...'
        '      INFO [...] ... DjVu 2550x3300, v24, 300 dpi, gamma=2.2'
        '      INCL [...] ... Indirection chunk --> {shared_anno.iff}'
        '      Sjbz [...] ... JB2 bilevel data'
        '      TXTz [...] ... Hidden text (text, etc.)'
        '    FORM:DJVU [...] {p0003.djvu}...'
        '      INFO [...] ... DjVu 2550x3300, v24, 300 dpi, gamma=2.2'
        '      INCL [...] ... Indirection chunk --> {shared_anno.iff}'
        '      Sjbz [...] ... JB2 bilevel data'
        '      FGbz [...] ... JB2 colors data, v0, 7 colors'
        '      BG44 [...] ... IW4 data #1, 97 slices, v1.2 (b&w), 213x275'
        '      TXTz [...] ... Hidden text (text, etc.)'
        '    FORM:DJVU [...] {p0004.djvu}...'
        '      INFO [...] ... DjVu 2550x3300, v24, 300 dpi, gamma=2.2'
        '      INCL [...] ... Indirection chunk --> {shared_anno.iff}'
        '      Sjbz [...] ... JB2 bilevel data'
        '      FGbz [...] ... JB2 colors data, v0, 1 colors'
        '      BG44 [...] ... IW4 data #1, 97 slices, v1.2 (color), 213x275'
        '      TXTz [...] ... Hidden text (text, etc.)'
        '    FORM:DJVU [...] {p0005.djvu}...'
        '      INFO [...] ... DjVu 2550x3300, v24, 300 dpi, gamma=2.2'
        '      INCL [...] ... Indirection chunk --> {shared_anno.iff}'
        '      Sjbz [...] ... JB2 bilevel data'
        '      ANTz [...] ... Page annotation (hyperlinks, etc.)'
        '      TXTz [...] ... Hidden text (text, etc.)'
        '    FORM:DJVU [...] {p0006.djvu}...'
        '      INFO [...] ... DjVu 2550x3300, v24, 300 dpi, gamma=2.2'
        '      INCL [...] ... Indirection chunk --> {shared_anno.iff}'
        '      Sjbz [...] ... JB2 bilevel data'
        '      FGbz [...] ... JB2 colors data, v0, 1 colors'
        '      BG44 [...] ... IW4 data #1, 72 slices, v1.2 (color), 850x1100'
        '      BG44 [...] ... IW4 data #2, 11 slices'
        '      BG44 [...] ... IW4 data #3, 10 slices'
        '      BG44 [...] ... IW4 data #4, 10 slices'
        '      TXTz [...] ... Hidden text (text, etc.)'
        >>> del tmp

        >>> tmp = NamedTemporaryFile()
        >>> job = document.save(tmp.file, pages=(0,))
        >>> type(job) == SaveJob
        True
        >>> job.is_done, job.is_error
        (True, False)
        >>> tmp.flush()
        >>> stdout, stderr = Popen(['djvudump', tmp.name], stdout=PIPE, stderr=PIPE, env={}).communicate()
        >>> stderr
        ''
        >>> for line in stdout.splitlines(): print repr(line) # doctest: +REPORT_NDIFF,+ELLIPSIS
        ...
        '  FORM:DJVM [...] '
        '    DIRM [...] ... Document directory (bundled, 2 files 1 pages)'
        '    FORM:DJVI [...] {shared_anno.iff}...'
        '      ANTz [...] ... Page annotation (hyperlinks, etc.)'
        '    FORM:DJVU [...] {p0001.djvu}...'
        '      INFO [...] ... DjVu 2550x3300, v24, 300 dpi, gamma=2.2'
        '      INCL [...] ... Indirection chunk --> {shared_anno.iff}'
        '      Sjbz [...] ... JB2 bilevel data'
        '      TXTz [...] ... Hidden text (text, etc.)'
        >>> del tmp

        >>> tmpdir = mkdtemp()
        >>> tmpfname = path_join(tmpdir, 'index.djvu')
        >>> job = document.save(indirect = tmpfname)
        >>> type(job) == SaveJob
        True
        >>> job.is_done, job.is_error
        (True, False)
        >>> stdout, stderr = Popen(['djvudump', tmpfname], stdout=PIPE, stderr=PIPE, env={}).communicate()
        >>> stderr
        ''
        >>> for line in stdout.splitlines(): print repr(line) # doctest: +REPORT_NDIFF,+ELLIPSIS
        ...
        '  FORM:DJVM [...] '
        '    DIRM [...] ... Document directory (indirect, 7 files 6 pages)'
        '      shared_anno.iff -> shared_anno.iff'
        '      p0001.djvu -> p0001.djvu'
        '      p0002.djvu -> p0002.djvu'
        '      p0003.djvu -> p0003.djvu'
        '      p0004.djvu -> p0004.djvu'
        '      p0005.djvu -> p0005.djvu'
        '      p0006.djvu -> p0006.djvu'
        '    NAVM [...] '
        >>> rmtree(tmpdir)

        >>> tmpdir = mkdtemp()
        >>> tmpfname = path_join(tmpdir, 'index.djvu')
        >>> job = document.save(indirect = tmpfname, pages = (0,))
        >>> type(job) == SaveJob
        True
        >>> job.is_done, job.is_error
        (True, False)
        >>> stdout, stderr = Popen(['djvudump', tmpfname], stdout=PIPE, stderr=PIPE, env={}).communicate()
        >>> stderr
        ''
        >>> for line in stdout.splitlines(): print repr(line) # doctest: +REPORT_NDIFF,+ELLIPSIS
        ...
        '  FORM:DJVM [...] '
        '    DIRM [...] ... Document directory (indirect, 2 files 1 pages)'
        '      shared_anno.iff -> shared_anno.iff'
        '      p0001.djvu -> p0001.djvu'
        >>> rmtree(tmpdir)
        '''

    def test_export_ps(self):
        r'''
        >>> import sys
        >>> context = Context()
        >>> document = context.new_document(FileUri(images + 'test0.djvu'))
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
        6
        >>> len(document.files)
        7

        >>> from tempfile import NamedTemporaryFile
        >>> from subprocess import Popen, PIPE
        >>> from pprint import pprint

        >>> tmp = NamedTemporaryFile()
        >>> job = document.export_ps(tmp.file)
        >>> type(job) == SaveJob
        True
        >>> job.is_done, job.is_error
        (True, False)
        >>> tmp.flush()
        >>> stdout, stderr = Popen(['ps2ascii', tmp.name], stdout = PIPE, stderr = PIPE, env={}).communicate()
        >>> stderr
        ''
        >>> stdout
        '\x0c\x0c\x0c\x0c\x0c\x0c'
        >>> del tmp

        >>> tmp = NamedTemporaryFile()
        >>> job = document.export_ps(tmp.file, pages = (2,), text = True)
        >>> type(job) == SaveJob
        True
        >>> job.is_done, job.is_error
        (True, False)
        >>> tmp.flush()
        >>> stdout, stderr = Popen(['ps2ascii', tmp.name], stdout = PIPE, stderr = PIPE, env={}).communicate()
        >>> stderr
        ''
        >>> for line in stdout.splitlines(): print repr(line.replace('  ', ' ')) # doctest: +REPORT_NDIFF
        ''
        ''
        ' 3C'
        ' red green blue cyan magenta yellow'
        ''
        ' red green blue cyan magenta yellow'
        ''
        ' 3\x0c'
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
        >>> document = context.new_document(FileUri(images + 'test1.djvu'))
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
        MemoryError: Unable to allocate 30000000000 bytes for an image memory

        >>> page_job.render(RENDER_COLOR, (0, 0, 10, 10), (0, 0, 4, 4), PixelFormatGrey(), 1)
        '\xff\xff\xff\xff\xff\xff\xff\xef\xff\xff\xff\xa4\xff\xff\xff\xb8'

        >>> from array import array
        >>> buffer = array('B', '\0')
        >>> page_job.render(RENDER_COLOR, (0, 0, 10, 10), (0, 0, 4, 4), PixelFormatGrey(), 1, buffer)
        Traceback (most recent call last):
        ...
        ValueError: Image buffer is too small (16 > 1)

        >>> buffer = array('B', '\0' * 16)
        >>> page_job.render(RENDER_COLOR, (0, 0, 10, 10), (0, 0, 4, 4), PixelFormatGrey(), 1, buffer) is buffer
        True
        >>> buffer.tostring()
        '\xff\xff\xff\xff\xff\xff\xff\xef\xff\xff\xff\xa4\xff\xff\xff\xb8'

        '''

class ThumbnailTest:

    r'''
    >>> context = Context()
    >>> document = context.new_document(FileUri(images + 'test1.djvu'))
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

    >>> from array import array
    >>> buffer = array('B', '\0')
    >>> (w, h, r), pixels = thumbnail.render((5, 5), PixelFormatGrey(), buffer=buffer)
    Traceback (most recent call last):
    ...
    ValueError: Image buffer is too small (25 > 1)

    >>> buffer = array('B', '\0' * 25)
    >>> (w, h, r), pixels = thumbnail.render((5, 5), PixelFormatGrey(), buffer=buffer)
    >>> pixels is buffer
    True
    >>> buffer[:15].tostring()
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
    ...   message.stream.write(file(images + 'test1.djvu').read())
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

def test_metadata():

    model_metadata = {
        'English': 'eggs',
        u'Русский': u'яйца',
    }
    test_script = 'set-meta\n%s\n.\n' % '\n'.join('|%s| %s' % (k, v) for k, v in model_metadata.iteritems()).encode('UTF-8')
    test_file = create_djvu(test_script)
    context = Context()
    document = context.new_document(FileUri(test_file.name))
    message = document.get_message()
    assert_equal(type(message), DocInfoMessage)
    annotations = document.annotations
    assert_equal(type(annotations), DocumentAnnotations)
    annotations.wait()
    metadata = annotations.metadata
    assert_equal(type(metadata), Metadata)
    assert_equal(len(metadata), len(model_metadata))
    assert_equal(sorted(metadata), sorted(model_metadata))
    assert_equal(sorted(metadata.iterkeys()), sorted(model_metadata.iterkeys()))
    assert_equal(sorted(metadata.keys()), sorted(model_metadata.keys()))
    assert_equal(sorted(metadata.values()), sorted(model_metadata.values()))
    assert_equal(sorted(metadata.items()), sorted(model_metadata.items()))
    for k in metadata:
        assert_equal(type(k), unicode)
        assert_equal(type(metadata[k]), unicode)
    for k in None, 42, '+'.join(model_metadata):
        assert_raises(KeyError, lambda: metadata[k])

class SexprTest:
    r'''
    >>> context = Context()
    >>> document = context.new_document(FileUri(images + 'test0.djvu'))
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
    Expression(((Symbol('metadata'), (Symbol('ModDate'), '2010-06-24 01:17:29+02:00'), (Symbol('CreationDate'), '2010-06-24 01:17:29+02:00'), (Symbol('Producer'), 'pdfTeX-1.40.10'), (Symbol('Creator'), 'LaTeX with hyperref package'), (Symbol('Author'), 'Jakub Wilk')), (Symbol('xmp'), '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"><rdf:Description rdf:about=""><xmpMM:History xmlns:xmpMM="http://ns.adobe.com/xap/1.0/mm/"><rdf:Seq><rdf:li xmlns:stEvt="http://ns.adobe.com/xap/1.0/sType/ResourceEvent#" stEvt:action="converted" stEvt:parameters="from application/pdf to image/vnd.djvu" softwareAgent="pdf2djvu 0.7.4 (DjVuLibre 3.5.22, poppler 0.12.4, GraphicsMagick++ 1.3.12, GNOME XSLT 1.1.26, GNOME XML 2.7.7)" when="2010-06-23T23:17:36+00:00"/></rdf:Seq></xmpMM:History><dc:creator xmlns:dc="http://purl.org/dc/elements/1.1/">Jakub Wilk</dc:creator><dc:format xmlns:dc="http://purl.org/dc/elements/1.1/">image/vnd.djvu</dc:format><pdf:Producer xmlns:pdf="http://ns.adobe.com/pdf/1.3/">pdfTeX-1.40.10</pdf:Producer><xmp:CreatorTool xmlns:xmp="http://ns.adobe.com/xap/1.0/">LaTeX with hyperref package</xmp:CreatorTool><xmp:CreateDate xmlns:xmp="http://ns.adobe.com/xap/1.0/">2010-06-24T01:17:29+02:00</xmp:CreateDate><xmp:ModifyDate xmlns:xmp="http://ns.adobe.com/xap/1.0/">2010-06-24T01:17:29+02:00</xmp:ModifyDate><xmp:MetadataDate xmlns:xmp="http://ns.adobe.com/xap/1.0/">2010-06-23T23:17:36+00:00</xmp:MetadataDate></rdf:Description></rdf:RDF>\n')))

    >>> metadata = anno.metadata
    >>> type(metadata) == Metadata
    True

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
    Expression((Symbol('bookmarks'), ('A', '#p0001.djvu'), ('B', '#p0002.djvu'), ('C', '#p0003.djvu'), ('D', '#p0004.djvu'), ('E', '#p0005.djvu', ('E1', '#p0005.djvu'), ('E2', '#p0005.djvu')), ('F', '#p0006.djvu')))

    >>> page = document.pages[4]
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
    Expression(((Symbol('metadata'), (Symbol('ModDate'), '2010-06-24 01:17:29+02:00'), (Symbol('CreationDate'), '2010-06-24 01:17:29+02:00'), (Symbol('Producer'), 'pdfTeX-1.40.10'), (Symbol('Creator'), 'LaTeX with hyperref package'), (Symbol('Author'), 'Jakub Wilk')), (Symbol('xmp'), '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"><rdf:Description rdf:about=""><xmpMM:History xmlns:xmpMM="http://ns.adobe.com/xap/1.0/mm/"><rdf:Seq><rdf:li xmlns:stEvt="http://ns.adobe.com/xap/1.0/sType/ResourceEvent#" stEvt:action="converted" stEvt:parameters="from application/pdf to image/vnd.djvu" softwareAgent="pdf2djvu 0.7.4 (DjVuLibre 3.5.22, poppler 0.12.4, GraphicsMagick++ 1.3.12, GNOME XSLT 1.1.26, GNOME XML 2.7.7)" when="2010-06-23T23:17:36+00:00"/></rdf:Seq></xmpMM:History><dc:creator xmlns:dc="http://purl.org/dc/elements/1.1/">Jakub Wilk</dc:creator><dc:format xmlns:dc="http://purl.org/dc/elements/1.1/">image/vnd.djvu</dc:format><pdf:Producer xmlns:pdf="http://ns.adobe.com/pdf/1.3/">pdfTeX-1.40.10</pdf:Producer><xmp:CreatorTool xmlns:xmp="http://ns.adobe.com/xap/1.0/">LaTeX with hyperref package</xmp:CreatorTool><xmp:CreateDate xmlns:xmp="http://ns.adobe.com/xap/1.0/">2010-06-24T01:17:29+02:00</xmp:CreateDate><xmp:ModifyDate xmlns:xmp="http://ns.adobe.com/xap/1.0/">2010-06-24T01:17:29+02:00</xmp:ModifyDate><xmp:MetadataDate xmlns:xmp="http://ns.adobe.com/xap/1.0/">2010-06-23T23:17:36+00:00</xmp:MetadataDate></rdf:Description></rdf:RDF>\n'), (Symbol('maparea'), '#p0002.djvu', '', (Symbol('rect'), 587, 2346, 60, 79), (Symbol('border'), Symbol('#ff0000'))), (Symbol('maparea'), 'http://jwilk.net/', '', (Symbol('rect'), 458, 1910, 1061, 93), (Symbol('border'), Symbol('#00ffff')))))

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
    [Expression((Symbol('maparea'), '#p0002.djvu', '', (Symbol('rect'), 587, 2346, 60, 79), (Symbol('border'), Symbol('#ff0000')))), Expression((Symbol('maparea'), 'http://jwilk.net/', '', (Symbol('rect'), 458, 1910, 1061, 93), (Symbol('border'), Symbol('#00ffff'))))]

    >>> text = page.text
    >>> type(text) == PageText
    True
    >>> text.wait()
    >>> text_s = text.sexpr
    >>> text_s_detail = [PageText(page, details).sexpr for details in (TEXT_DETAILS_PAGE, TEXT_DETAILS_COLUMN, TEXT_DETAILS_REGION, TEXT_DETAILS_PARAGRAPH, TEXT_DETAILS_LINE, TEXT_DETAILS_WORD, TEXT_DETAILS_CHARACTER, TEXT_DETAILS_ALL)]
    >>> text_s_detail[0] == text_s_detail[1] == text_s_detail[2] == text_s_detail[3]
    True
    >>> text_s_detail[0]
    Expression((Symbol('page'), 0, 0, 2550, 3300, '5E \n5.1 E1 \n\xe2\x86\x921 \n5.2 E2 \nhttp://jwilk.net/ \n5 \n'))
    >>> text_s_detail[4]
    Expression((Symbol('page'), 0, 0, 2550, 3300, (Symbol('line'), 462, 2726, 615, 2775, '5E '), (Symbol('line'), 462, 2544, 663, 2586, '5.1 E1 '), (Symbol('line'), 466, 2349, 631, 2421, '\xe2\x86\x921 '), (Symbol('line'), 462, 2124, 665, 2166, '5.2 E2 '), (Symbol('line'), 465, 1911, 1504, 2000, 'http://jwilk.net/ '), (Symbol('line'), 1259, 374, 1280, 409, '5 ')))
    >>> text_s_detail[5] == text_s_detail[6] == text_s_detail[7] == text_s
    True
    >>> text_s
    Expression((Symbol('page'), 0, 0, 2550, 3300, (Symbol('line'), 462, 2726, 615, 2775, (Symbol('word'), 462, 2726, 615, 2775, '5E')), (Symbol('line'), 462, 2544, 663, 2586, (Symbol('word'), 462, 2544, 533, 2586, '5.1'), (Symbol('word'), 596, 2545, 663, 2586, 'E1')), (Symbol('line'), 466, 2349, 631, 2421, (Symbol('word'), 466, 2349, 631, 2421, '\xe2\x86\x921')), (Symbol('line'), 462, 2124, 665, 2166, (Symbol('word'), 462, 2124, 535, 2166, '5.2'), (Symbol('word'), 596, 2125, 665, 2166, 'E2')), (Symbol('line'), 465, 1911, 1504, 2000, (Symbol('word'), 465, 1911, 1504, 2000, 'http://jwilk.net/')), (Symbol('line'), 1259, 374, 1280, 409, (Symbol('word'), 1259, 374, 1280, 409, '5'))))
    >>> PageText(page, 'eggs')
    Traceback (most recent call last):
    ...
    TypeError: details must be a symbol or none
    >>> PageText(page, Symbol('eggs'))
    Traceback (most recent call last):
    ...
    ValueError: details must be equal to TEXT_DETAILS_PAGE, or TEXT_DETAILS_COLUMN, or TEXT_DETAILS_REGION, or TEXT_DETAILS_PARAGRAPH, or TEXT_DETAILS_LINE, or TEXT_DETAILS_WORD, or TEXT_DETAILS_CHARACTER or TEXT_DETAILS_ALL
    '''

# vim:ts=4 sw=4 et
