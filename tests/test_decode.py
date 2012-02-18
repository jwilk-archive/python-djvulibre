# encoding=UTF-8
# Copyright © 2007, 2008, 2009, 2010, 2011, 2012 Jakub Wilk <jwilk@jwilk.net>
#
# This package is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This package is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

from __future__ import with_statement

import array
import os
import shutil
import subprocess as ipc
import sys
import tempfile

from djvu.decode import *
from djvu.sexpr import *

from common import *

images = os.path.join(os.path.dirname(__file__), 'images', '')

def create_djvu(commands='', sexpr=''):
    skip_unless_command_exists('djvused')
    if sexpr:
        commands += '\nset-ant\n%s\n.\n' % sexpr
    file = tempfile.NamedTemporaryFile(prefix='test', suffix='djvu')
    file.seek(0)
    file.write(blob(
        0x41, 0x54, 0x26, 0x54, 0x46, 0x4f, 0x52, 0x4d, 0x00, 0x00, 0x00, 0x22, 0x44, 0x4a, 0x56, 0x55,
        0x49, 0x4e, 0x46, 0x4f, 0x00, 0x00, 0x00, 0x0a, 0x00, 0x01, 0x00, 0x01, 0x18, 0x00, 0x2c, 0x01,
        0x16, 0x01, 0x53, 0x6a, 0x62, 0x7a, 0x00, 0x00, 0x00, 0x04, 0xbc, 0x73, 0x1b, 0xd7,
    ))
    file.flush()
    djvused = ipc.Popen(['djvused', '-s', file.name], stdin=ipc.PIPE, stdout=ipc.PIPE, stderr=ipc.PIPE)
    djvused.stdin.write(commands.encode(locale_encoding))
    djvused.stdin.close()
    assert_equal(djvused.wait(), 0)
    assert_equal(djvused.stdout.read(), ''.encode(locale_encoding))
    assert_equal(djvused.stderr.read(), ''.encode(locale_encoding))
    return file

def test_context_cache():
    context = Context()
    assert_equal(context.cache_size, 10 << 20)
    for n in -100, 0, 1 << 31:
        with raises(ValueError, '0 < cache_size < (2 ** 31) must be satisfied'):
            context.cache_size = n
    with raises(ValueError, '0 < cache_size < (2 ** 31) must be satisfied'):
        context.cache_size = 0
    n = 1
    while n < (1 << 31):
        context.cache_size = n
        assert_equal(context.cache_size, n)
        n = (n + 1) * 2 - 1
    context.clear_cache()

class test_documents:

    def test_bad_new(self):
        with raises(TypeError, "cannot create 'djvu.decode.Document' instances"):
            Document()

    def test_nonexistent(self):
        skip_unless_c_messages()
        context = Context()
        with raises(JobFailed):
            document = context.new_document(FileUri('__nonexistent__'))
        message = context.get_message()
        assert_equal(type(message), ErrorMessage)
        assert_equal(type(message.message), unicode)
        assert_equal(message.message, "[1-11711] Failed to open '__nonexistent__': No such file or directory.")
        assert_equal(str(message), message.message)
        assert_equal(unicode(message), message.message)

    def test_nonexistent_ja(self):
        skip_unless_c_messages()
        skip_unless_translation_exists('ja_JP.UTF-8')
        context = Context()
        with amended_locale(LC_ALL='ja_JP.UTF-8'):
            with raises(JobFailed):
                document = context.new_document(FileUri('__nonexistent__'))
            message = context.get_message()
            assert_equal(type(message), ErrorMessage)
            assert_equal(type(message.message), unicode)
            assert_equal(message.message, u("[1-11711] Failed to open '__nonexistent__': そのようなファイルやディレクトリはありません."))
            assert_equal(str(message), "[1-11711] Failed to open '__nonexistent__': そのようなファイルやディレクトリはありません.")
            assert_equal(unicode(message), message.message)

    def test_new_document(self):
        context = Context()
        document = context.new_document(FileUri(images + 'test1.djvu'))
        assert_equal(type(document), Document)
        message = document.get_message()
        assert_equal(type(message), DocInfoMessage)
        assert_true(document.decoding_done)
        assert_false(document.decoding_error)
        assert_equal(document.decoding_status, JobOK)
        assert_equal(document.type, DOCUMENT_TYPE_SINGLE_PAGE)
        assert_equal(len(document.pages), 1)
        assert_equal(len(document.files), 1)

        decoding_job = document.decoding_job
        assert_true(decoding_job.is_done)
        assert_false(decoding_job.is_error)
        assert_equal(decoding_job.status, JobOK)

        file = document.files[0]
        assert_true(type(file) is File)
        assert_true(file.document is document)
        assert_true(file.get_info() is None)
        assert_equal(file.type, 'P')
        assert_equal(file.n_page, 0)
        page = file.page
        assert_equal(type(page), Page)
        assert_true(page.document is document)
        assert_equal(page.n, 0)
        assert_true(file.size is None)
        assert_equal(file.id, u('test1.djvu'))
        assert_equal(type(file.id), unicode)
        assert_equal(file.name, u('test1.djvu'))
        assert_equal(type(file.name), unicode)
        assert_equal(file.title, u('test1.djvu'))
        assert_equal(type(file.title), unicode)

        dump = document.files[0].dump
        assert_equal(type(dump), unicode)
        assert_equal(
            [line for line in dump.splitlines()], [
                u('  FORM:DJVU [83] '),
                u('    INFO [10]         DjVu 64x48, v24, 300 dpi, gamma=2.2'),
                u('    Sjbz [53]         JB2 bilevel data'),
            ]
        )

        page = document.pages[0]
        assert_equal(type(page), Page)
        assert_true(page.document is document)
        assert_true(page.get_info() is None)
        assert_equal(page.width, 64)
        assert_equal(page.height, 48)
        assert_equal(page.size, (64, 48))
        assert_equal(page.dpi, 300)
        assert_equal(page.rotation, 0)
        assert_equal(page.version, 24)
        file = page.file
        assert_equal(type(file), File)
        assert_equal(file.id, u('test1.djvu'))
        assert_equal(type(file.id), unicode)

        dump = document.files[0].dump
        assert_equal(type(dump), unicode)
        assert_equal(
            [line for line in dump.splitlines()], [
                u('  FORM:DJVU [83] '),
                u('    INFO [10]         DjVu 64x48, v24, 300 dpi, gamma=2.2'),
                u('    Sjbz [53]         JB2 bilevel data'),
            ]
        )

        assert_true(document.get_message(wait=False) is None)
        assert_true(context.get_message(wait=False) is None)

        with raises(IndexError, 'file number out of range'):
            document.files[-1].get_info()
        assert_true(document.get_message(wait=False) is None)
        assert_true(context.get_message(wait=False) is None)

        with raises(IndexError, 'page number out of range'):
            document.pages[-1]
        with raises(IndexError, 'page number out of range'):
            document.pages[1]

        assert_true(document.get_message(wait=False) is None)
        assert_true(context.get_message(wait=False) is None)

    def test_save(self):
        skip_unless_command_exists('djvudump')
        context = Context()
        original_filename = images + 'test0.djvu'
        document = context.new_document(FileUri(original_filename))
        message = document.get_message()
        assert_equal(type(message), DocInfoMessage)
        assert_true(document.decoding_done)
        assert_false(document.decoding_error)
        assert_equal(document.decoding_status, JobOK)
        assert_equal(document.type, DOCUMENT_TYPE_BUNDLED)
        assert_equal(len(document.pages), 6)
        assert_equal(len(document.files), 7)

        stdout0, stderr0 = ipc.Popen(['djvudump', original_filename], stdout=ipc.PIPE, stderr=ipc.PIPE, env={}).communicate()
        assert_equal(stderr0, b(''))
        stdout0 = stdout0.replace(b('\r\n'), b('\n'))

        tmpdir = tempfile.mkdtemp()
        try:
            tmp = open(os.path.join(tmpdir, 'tmp.djvu'), 'wb')
            job = document.save(tmp)
            assert_equal(type(job), SaveJob)
            assert_true(job.is_done)
            assert_false(job.is_error)
            tmp.close()
            stdout, stderr = ipc.Popen(['djvudump', tmp.name], stdout=ipc.PIPE, stderr=ipc.PIPE, env={}).communicate()
            assert_equal(stderr, b(''))
            stdout = stdout.replace(b('\r\n'), b('\n'))
            assert_equal(stdout, stdout0)
        finally:
            shutil.rmtree(tmpdir)
            tmp = None

        tmpdir = tempfile.mkdtemp()
        try:
            tmp = open(os.path.join(tmpdir, 'tmp.djvu'), 'wb')
            job = document.save(tmp, pages=(0,))
            assert_equal(type(job), SaveJob)
            assert_true(job.is_done)
            assert_false(job.is_error)
            tmp.close()
            stdout, stderr = ipc.Popen(['djvudump', tmp.name], stdout=ipc.PIPE, stderr=ipc.PIPE, env={}).communicate()
            assert_equal(stderr, b(''))
            stdout = stdout.replace(b('\r\n'), b('\n'))
            stdout0 = stdout0.split(b('\n'))
            stdout = stdout.split(b('\n'))
            stdout[4] = stdout[4].replace(b(' (1)'), b(''))
            assert_equal(len(stdout), 10)
            assert_equal(stdout[3:-1], stdout0[4:10])
            assert_equal(stdout[-1], b(''))
        finally:
            shutil.rmtree(tmpdir)
            tmp = None

        tmpdir = tempfile.mkdtemp()
        try:
            tmpfname = os.path.join(tmpdir, 'index.djvu')
            job = document.save(indirect=tmpfname)
            assert_equal(type(job), SaveJob)
            assert_true(job.is_done)
            assert_false(job.is_error)
            stdout, stderr = ipc.Popen(['djvudump', tmpfname], stdout=ipc.PIPE, stderr=ipc.PIPE, env={}).communicate()
            assert_equal(stderr, b(''))
            stdout = stdout.replace(b('\r\n'), b('\n'))
            stdout = stdout.split(b('\n'))
            stdout0 = (
                [b('      shared_anno.iff -> shared_anno.iff')] +
                [b('      p%04d.djvu -> p%04d.djvu' % (n, n)) for n in range(1, 7)]
            )
            assert_equal(len(stdout), 11)
            assert_equal(stdout[2:-2], stdout0)
            assert_equal(stdout[-1], b(''))
        finally:
            shutil.rmtree(tmpdir)

        tmpdir = tempfile.mkdtemp()
        try:
            tmpfname = os.path.join(tmpdir, 'index.djvu')
            job = document.save(indirect=tmpfname, pages=(0,))
            assert_equal(type(job), SaveJob)
            assert_true(job.is_done)
            assert_false(job.is_error)
            stdout, stderr = ipc.Popen(['djvudump', tmpfname], stdout=ipc.PIPE, stderr=ipc.PIPE, env={}).communicate()
            stdout = stdout.replace(b('\r\n'), b('\n'))
            assert_equal(stderr, b(''))
            stdout = stdout.split(b('\n'))
            assert_equal(len(stdout), 5)
            assert_equal(stdout[2], b('      shared_anno.iff -> shared_anno.iff'))
            assert_equal(stdout[3], b('      p0001.djvu -> p0001.djvu'))
            assert_equal(stdout[-1], b(''))
        finally:
            shutil.rmtree(tmpdir)

    def test_export_ps(self):
        skip_unless_command_exists('ps2ascii')
        context = Context()
        document = context.new_document(FileUri(images + 'test0.djvu'))
        message = document.get_message()
        assert_equal(type(message), DocInfoMessage)
        assert_true(document.decoding_done)
        assert_false(document.decoding_error)
        assert_equal(document.decoding_status, JobOK)
        assert_equal(document.type, DOCUMENT_TYPE_BUNDLED)
        assert_equal(len(document.pages), 6)
        assert_equal(len(document.files), 7)

        tmp = tempfile.NamedTemporaryFile()
        try:
            job = document.export_ps(tmp.file)
            assert_equal(type(job), SaveJob)
            assert_true(job.is_done)
            assert_false(job.is_error)
            stdout, stderr = ipc.Popen(['ps2ascii', tmp.name], stdout=ipc.PIPE, stderr=ipc.PIPE, env={}).communicate()
            assert_equal(stderr, b(''))
            assert_equal(stdout, b('\x0c') * 6)
        finally:
            tmp.close()

        tmp = tempfile.NamedTemporaryFile()
        try:
            job = document.export_ps(tmp.file, pages=(2,), text=True)
            assert_equal(type(job), SaveJob)
            assert_true(job.is_done)
            assert_false(job.is_error)
            stdout, stderr = ipc.Popen(['ps2ascii', tmp.name], stdout=ipc.PIPE, stderr=ipc.PIPE, env={}).communicate()
            assert_equal(stderr, b(''))
            stdout = stdout.split(b('\n'))
            stdout = [b(' ').join(line.split()) for line in stdout]
            assert_equal(stdout, [
                b(''),
                b(''),
                b('3C'),
                b('red green blue cyan magenta yellow'),
                b(''),
                b('red green blue cyan magenta yellow'),
                b(''),
                b('3'),
            ])
        finally:
            del tmp

class test_pixel_formats():

    def test_bad_new(self):
        with raises(TypeError, "cannot create 'djvu.decode.PixelFormat' instances"):
            PixelFormat()

    def test_rgb(self):
        pf = PixelFormatRgb()
        assert_equal(repr(pf), "djvu.decode.PixelFormatRgb(byte_order = 'RGB', bpp = 24)")
        pf = PixelFormatRgb('RGB')
        assert_equal(repr(pf), "djvu.decode.PixelFormatRgb(byte_order = 'RGB', bpp = 24)")
        pf = PixelFormatRgb('BGR')
        assert_equal(repr(pf), "djvu.decode.PixelFormatRgb(byte_order = 'BGR', bpp = 24)")

    def test_rgb_mask(self):
        pf = PixelFormatRgbMask(0xff, 0xf00, 0x1f000, 0, 16)
        assert_equal(repr(pf), "djvu.decode.PixelFormatRgbMask(red_mask = 0x00ff, green_mask = 0x0f00, blue_mask = 0xf000, xor_value = 0x0000, bpp = 16)")
        pf = PixelFormatRgbMask(0xff000000, 0xff0000, 0xff00, 0xff, 32)
        assert_equal(repr(pf), "djvu.decode.PixelFormatRgbMask(red_mask = 0xff000000, green_mask = 0x00ff0000, blue_mask = 0x0000ff00, xor_value = 0x000000ff, bpp = 32)")

    def test_grey(self):
        pf = PixelFormatGrey()
        assert_equal(repr(pf), "djvu.decode.PixelFormatGrey(bpp = 8)")

    def test_palette(self):
        with raises(KeyError, repr((0, 0, 0))):
            pf = PixelFormatPalette({})
        data = dict(((i, j, k), i + 7 * j + 37 + k) for i in range(6) for j in range(6) for k in range(6))
        pf = PixelFormatPalette(data)
        data_repr = ', '.join('%r: 0x%02x' % (k, v) for k, v in sorted(data.items()))
        assert_equal(repr(pf), "djvu.decode.PixelFormatPalette({%s}, bpp = 8)" % data_repr)

    def test_packed_bits(self):
        pf = PixelFormatPackedBits('<')
        assert_equal(repr(pf), "djvu.decode.PixelFormatPackedBits('<')")
        assert_equal(pf.bpp, 1)
        pf = PixelFormatPackedBits('>')
        assert_equal(repr(pf), "djvu.decode.PixelFormatPackedBits('>')")
        assert_equal(pf.bpp, 1)

class test_page_jobs():

    def test_bad_new(self):
        with raises(TypeError, "cannot create 'djvu.decode.PageJob' instances"):
            PageJob()

    def test_decode(self):
        context = Context()
        document = context.new_document(FileUri(images + 'test1.djvu'))
        message = document.get_message()
        assert_equal(type(message), DocInfoMessage)
        page_job = document.pages[0].decode()
        assert_true(page_job.is_done)
        assert_equal(type(page_job), PageJob)
        assert_true(page_job.is_done)
        assert_false(page_job.is_error)
        assert_equal(page_job.status, JobOK)
        assert_equal(page_job.width, 64)
        assert_equal(page_job.height, 48)
        assert_equal(page_job.size, (64, 48))
        assert_equal(page_job.dpi, 300)
        assert_equal(page_job.gamma, 2.2)
        assert_equal(page_job.version, 24)
        assert_equal(page_job.type, PAGE_TYPE_BITONAL)
        assert_equal((page_job.rotation, page_job.initial_rotation), (0, 0))
        with raises(ValueError, 'rotation must be equal to 0, 90, 180, or 270'):
            page_job.rotation = 100
        page_job.rotation = 180
        assert_equal((page_job.rotation, page_job.initial_rotation), (180, 0))
        del page_job.rotation
        assert_equal((page_job.rotation, page_job.initial_rotation), (0, 0))

        with raises(ValueError, 'page_rect width/height must be a positive integer'):
            page_job.render(RENDER_COLOR, (0, 0, -1, -1), (0, 0, 10, 10), PixelFormatRgb())

        with raises(ValueError, 'render_rect width/height must be a positive integer'):
            page_job.render(RENDER_COLOR, (0, 0, 10, 10), (0, 0, -1, -1), PixelFormatRgb())

        with raises(ValueError, 'render_rect must be inside page_rect'):
            page_job.render(RENDER_COLOR, (0, 0, 10, 10), (2, 2, 10, 10), PixelFormatRgb())

        with raises(ValueError, 'row_alignment must be a positive integer'):
            page_job.render(RENDER_COLOR, (0, 0, 10, 10), (0, 0, 10, 10), PixelFormatRgb(), -1)

        with raises(MemoryError, regex='^Unable to allocate [0-9]+ bytes for an image memory$'):
            x = int((maxsize//2) ** 0.5)
            page_job.render(RENDER_COLOR, (0, 0, x, x), (0, 0, x, x), PixelFormatRgb(), 8)

        s = page_job.render(RENDER_COLOR, (0, 0, 10, 10), (0, 0, 4, 4), PixelFormatGrey(), 1)
        assert_equal(s, blob(0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xef, 0xff, 0xff, 0xff, 0xa4, 0xff, 0xff, 0xff, 0xb8))

        buffer = array.array('B', blob(0))
        with raises(ValueError, 'Image buffer is too small (16 > 1)'):
            page_job.render(RENDER_COLOR, (0, 0, 10, 10), (0, 0, 4, 4), PixelFormatGrey(), 1, buffer)

        buffer = array.array('B', blob(*([0] * 16)))
        assert_true(page_job.render(RENDER_COLOR, (0, 0, 10, 10), (0, 0, 4, 4), PixelFormatGrey(), 1, buffer) is buffer)
        s = buffer.tostring()
        assert_equal(s, blob(0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xef, 0xff, 0xff, 0xff, 0xa4, 0xff, 0xff, 0xff, 0xb8))

class test_thumbnails:

    def test(self):
        context = Context()
        document = context.new_document(FileUri(images + 'test1.djvu'))
        message = document.get_message()
        assert_equal(type(message), DocInfoMessage)
        thumbnail = document.pages[0].thumbnail
        assert_equal(thumbnail.status, JobOK)
        assert_equal(thumbnail.calculate(), JobOK)
        message = document.get_message()
        assert_equal(type(message), ThumbnailMessage)
        assert_equal(message.thumbnail.page.n, 0)

        (w, h, r), pixels = thumbnail.render((5, 5), PixelFormatGrey(), dry_run=True)
        assert_equal((w, h, r), (5, 3, 5))
        assert_true(pixels is None)

        (w, h, r), pixels = thumbnail.render((5, 5), PixelFormatGrey())
        assert_equal((w, h, r), (5, 3, 5))
        assert_equal(pixels[:15], blob(0xff, 0xeb, 0xa7, 0xf2, 0xff, 0xff, 0xbf, 0x86, 0xbe, 0xff, 0xff, 0xe7, 0xd6, 0xe7, 0xff))

        buffer = array.array('B', blob(0))
        with raises(ValueError, 'Image buffer is too small (25 > 1)'):
            (w, h, r), pixels = thumbnail.render((5, 5), PixelFormatGrey(), buffer=buffer)

        buffer = array.array('B', blob(*([0] * 25)))
        (w, h, r), pixels = thumbnail.render((5, 5), PixelFormatGrey(), buffer=buffer)
        assert_true(pixels is buffer)
        s = buffer[:15].tostring()
        assert_equal(s, blob(0xff, 0xeb, 0xa7, 0xf2, 0xff, 0xff, 0xbf, 0x86, 0xbe, 0xff, 0xff, 0xe7, 0xd6, 0xe7, 0xff))

def test_jobs():

    with raises(TypeError, "cannot create 'djvu.decode.Job' instances"):
        Job()

    with raises(TypeError, "cannot create 'djvu.decode.DocumentDecodingJob' instances"):
        DocumentDecodingJob()

class test_affine_transforms():

    def test_bad_args(self):
        with raises(ValueError, 'need more than 2 values to unpack'):
            AffineTransform((1, 2), (3, 4, 5))

    def test1(self):
        af = AffineTransform((0, 0, 10, 10), (17, 42, 42, 100))
        assert_equal(type(af), AffineTransform)
        assert_equal(af((0, 0)), (17, 42))
        assert_equal(af((0, 10)), (17, 142))
        assert_equal(af((10, 0)), (59, 42))
        assert_equal(af((10, 10)), (59, 142))
        assert_equal(af((0, 0, 10, 10)), (17, 42, 42, 100))
        assert_equal(af(x for x in (0, 0, 10, 10)), (17, 42, 42, 100))
        assert_equal(af.apply((123, 456)), af((123, 456)))
        assert_equal(af.apply((12, 34, 56, 78)), af((12, 34, 56, 78)))
        assert_equal(af.inverse((17, 42)), (0, 0))
        assert_equal(af.inverse((17, 142)), (0, 10))
        assert_equal(af.inverse((59, 42)), (10, 0))
        assert_equal(af.inverse((59, 142)), (10, 10))
        assert_equal(af.inverse((17, 42, 42, 100)), (0, 0, 10, 10))
        assert_equal(af.inverse(x for x in (17, 42, 42, 100)), (0, 0, 10, 10))
        assert_equal(af.inverse(af((234, 567))), (234, 567))
        assert_equal(af.inverse(af((23, 45, 67, 78))), (23, 45, 67, 78))

class test_messages():

    def test_bad_new(self):
        with raises(TypeError, "cannot create 'djvu.decode.Message' instances"):
            Message()

class test_streams:

    def test_bad_new(self):
        with raises(TypeError, "Argument 'document' has incorrect type (expected djvu.decode.Document, got NoneType)"):
            Stream(None, 42)

    def test(self):
        context = Context()
        document = context.new_document('dummy://dummy.djvu')
        message = document.get_message()
        assert_equal(type(message), NewStreamMessage)
        assert_equal(message.name, 'dummy.djvu')
        assert_equal(message.uri, 'dummy://dummy.djvu')
        assert_equal(type(message.stream), Stream)

        with raises(NotAvailable):
            document.outline.sexpr
        with raises(NotAvailable):
            document.annotations.sexpr
        with raises(NotAvailable):
            document.pages[0].text.sexpr
        with raises(NotAvailable):
            document.pages[0].annotations.sexpr

        try:
            message.stream.write(open(images + 'test1.djvu', 'rb').read())
        finally:
            message.stream.close()
        with raises(IOError, 'I/O operation on closed file'):
            message.stream.write(b('eggs'))

        message = document.get_message()
        assert_equal(type(message), DocInfoMessage)

        outline = document.outline
        outline.wait()
        x = outline.sexpr
        assert_equal(x, Expression([]))
        anno = document.annotations
        anno.wait()
        x = anno.sexpr
        assert_equal(x, Expression([]))
        text = document.pages[0].text
        text.wait()
        x = text.sexpr
        assert_equal(x, Expression([]))
        anno = document.pages[0].annotations
        anno.wait()
        x = anno.sexpr
        assert_equal(x, Expression([]))

def test_metadata():

    model_metadata = {
        'English': 'eggs',
        u('Русский'): u('яйца'),
    }
    test_script = 'set-meta\n%s\n.\n' % '\n'.join('|%s| %s' % (k, v) for k, v in model_metadata.items())
    try:
        test_file = create_djvu(test_script)
    except UnicodeEncodeError:
        raise AssertionError('You need to run this test with an UTF-8 locale')
    try:
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
        if not py3k:
            assert_equal(sorted(metadata.iterkeys()), sorted(model_metadata.iterkeys()))
        assert_equal(sorted(metadata.keys()), sorted(model_metadata.keys()))
        if not py3k:
            assert_equal(sorted(metadata.itervalues()), sorted(model_metadata.itervalues()))
        assert_equal(sorted(metadata.values()), sorted(model_metadata.values()))
        if not py3k:
            assert_equal(sorted(metadata.iteritems()), sorted(model_metadata.iteritems()))
        assert_equal(sorted(metadata.items()), sorted(model_metadata.items()))
        for k in metadata:
            assert_equal(type(k), unicode)
            assert_equal(type(metadata[k]), unicode)
        for k in None, 42, '+'.join(model_metadata):
            with raises(KeyError, repr(k)):
                metadata[k]
    finally:
        test_file.close()

class test_sexpr:

    def test(self):
        context = Context()
        document = context.new_document(FileUri(images + 'test0.djvu'))
        assert_equal(type(document), Document)
        message = document.get_message()
        assert_equal(type(message), DocInfoMessage)

        anno = DocumentAnnotations(document, shared=False)
        assert_equal(type(anno), DocumentAnnotations)
        anno.wait()
        x = anno.sexpr
        assert_equal(x, Expression([]))

        anno = document.annotations
        assert_equal(type(anno), DocumentAnnotations)
        anno.wait()
        assert_true(anno.background_color is None)
        assert_true(anno.horizontal_align is None)
        assert_true(anno.vertical_align is None)
        assert_true(anno.mode is None)
        assert_true(anno.zoom is None)
        x = anno.sexpr
        assert_equal(repr(x), r"""Expression(((Symbol('metadata'), (Symbol('ModDate'), '2010-06-24 01:17:29+02:00'), (Symbol('CreationDate'), '2010-06-24 01:17:29+02:00'), (Symbol('Producer'), 'pdfTeX-1.40.10'), (Symbol('Creator'), 'LaTeX with hyperref package'), (Symbol('Author'), 'Jakub Wilk')), (Symbol('xmp'), '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"><rdf:Description rdf:about=""><xmpMM:History xmlns:xmpMM="http://ns.adobe.com/xap/1.0/mm/"><rdf:Seq><rdf:li xmlns:stEvt="http://ns.adobe.com/xap/1.0/sType/ResourceEvent#" stEvt:action="converted" stEvt:parameters="from application/pdf to image/vnd.djvu" softwareAgent="pdf2djvu 0.7.4 (DjVuLibre 3.5.22, poppler 0.12.4, GraphicsMagick++ 1.3.12, GNOME XSLT 1.1.26, GNOME XML 2.7.7)" when="2010-06-23T23:17:36+00:00"/></rdf:Seq></xmpMM:History><dc:creator xmlns:dc="http://purl.org/dc/elements/1.1/">Jakub Wilk</dc:creator><dc:format xmlns:dc="http://purl.org/dc/elements/1.1/">image/vnd.djvu</dc:format><pdf:Producer xmlns:pdf="http://ns.adobe.com/pdf/1.3/">pdfTeX-1.40.10</pdf:Producer><xmp:CreatorTool xmlns:xmp="http://ns.adobe.com/xap/1.0/">LaTeX with hyperref package</xmp:CreatorTool><xmp:CreateDate xmlns:xmp="http://ns.adobe.com/xap/1.0/">2010-06-24T01:17:29+02:00</xmp:CreateDate><xmp:ModifyDate xmlns:xmp="http://ns.adobe.com/xap/1.0/">2010-06-24T01:17:29+02:00</xmp:ModifyDate><xmp:MetadataDate xmlns:xmp="http://ns.adobe.com/xap/1.0/">2010-06-23T23:17:36+00:00</xmp:MetadataDate></rdf:Description></rdf:RDF>\n')))""")

        metadata = anno.metadata
        assert_equal(type(metadata), Metadata)

        hyperlinks = anno.hyperlinks
        assert_equal(type(hyperlinks), Hyperlinks)
        assert_equal(len(hyperlinks), 0)
        assert_equal(list(hyperlinks), [])

        outline = document.outline
        assert_equal(type(outline), DocumentOutline)
        outline.wait()
        x = outline.sexpr
        assert_equal(repr(x), r"""Expression((Symbol('bookmarks'), ('A', '#p0001.djvu'), ('B', '#p0002.djvu'), ('C', '#p0003.djvu'), ('D', '#p0004.djvu'), ('E', '#p0005.djvu', ('E1', '#p0005.djvu'), ('E2', '#p0005.djvu')), ('F', '#p0006.djvu')))""")

        page = document.pages[4]
        anno = page.annotations
        assert_equal(type(anno), PageAnnotations)
        anno.wait()
        assert_true(anno.background_color is None)
        assert_true(anno.horizontal_align is None)
        assert_true(anno.vertical_align is None)
        assert_true(anno.mode is None)
        assert_true(anno.zoom is None)
        x = anno.sexpr
        assert_equal(repr(x), r"""Expression(((Symbol('metadata'), (Symbol('ModDate'), '2010-06-24 01:17:29+02:00'), (Symbol('CreationDate'), '2010-06-24 01:17:29+02:00'), (Symbol('Producer'), 'pdfTeX-1.40.10'), (Symbol('Creator'), 'LaTeX with hyperref package'), (Symbol('Author'), 'Jakub Wilk')), (Symbol('xmp'), '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"><rdf:Description rdf:about=""><xmpMM:History xmlns:xmpMM="http://ns.adobe.com/xap/1.0/mm/"><rdf:Seq><rdf:li xmlns:stEvt="http://ns.adobe.com/xap/1.0/sType/ResourceEvent#" stEvt:action="converted" stEvt:parameters="from application/pdf to image/vnd.djvu" softwareAgent="pdf2djvu 0.7.4 (DjVuLibre 3.5.22, poppler 0.12.4, GraphicsMagick++ 1.3.12, GNOME XSLT 1.1.26, GNOME XML 2.7.7)" when="2010-06-23T23:17:36+00:00"/></rdf:Seq></xmpMM:History><dc:creator xmlns:dc="http://purl.org/dc/elements/1.1/">Jakub Wilk</dc:creator><dc:format xmlns:dc="http://purl.org/dc/elements/1.1/">image/vnd.djvu</dc:format><pdf:Producer xmlns:pdf="http://ns.adobe.com/pdf/1.3/">pdfTeX-1.40.10</pdf:Producer><xmp:CreatorTool xmlns:xmp="http://ns.adobe.com/xap/1.0/">LaTeX with hyperref package</xmp:CreatorTool><xmp:CreateDate xmlns:xmp="http://ns.adobe.com/xap/1.0/">2010-06-24T01:17:29+02:00</xmp:CreateDate><xmp:ModifyDate xmlns:xmp="http://ns.adobe.com/xap/1.0/">2010-06-24T01:17:29+02:00</xmp:ModifyDate><xmp:MetadataDate xmlns:xmp="http://ns.adobe.com/xap/1.0/">2010-06-23T23:17:36+00:00</xmp:MetadataDate></rdf:Description></rdf:RDF>\n'), (Symbol('maparea'), '#p0002.djvu', '', (Symbol('rect'), 587, 2346, 60, 79), (Symbol('border'), Symbol('#ff0000'))), (Symbol('maparea'), 'http://jwilk.net/', '', (Symbol('rect'), 458, 1910, 1061, 93), (Symbol('border'), Symbol('#00ffff')))))""")

        page_metadata = anno.metadata
        assert_equal(type(page_metadata), Metadata)
        assert_equal(page_metadata.keys(), metadata.keys())
        assert_equal([page_metadata[k] == metadata[k] for k in metadata], [True, True, True, True, True])

        hyperlinks = anno.hyperlinks
        assert_equal(type(hyperlinks), Hyperlinks)
        assert_equal(len(hyperlinks), 2)
        assert_equal(repr(list(hyperlinks)), r"""[Expression((Symbol('maparea'), '#p0002.djvu', '', (Symbol('rect'), 587, 2346, 60, 79), (Symbol('border'), Symbol('#ff0000')))), Expression((Symbol('maparea'), 'http://jwilk.net/', '', (Symbol('rect'), 458, 1910, 1061, 93), (Symbol('border'), Symbol('#00ffff'))))]""")

        text = page.text
        assert_equal(type(text), PageText)
        text.wait()
        text_s = text.sexpr
        text_s_detail = [PageText(page, details).sexpr for details in (TEXT_DETAILS_PAGE, TEXT_DETAILS_COLUMN, TEXT_DETAILS_REGION, TEXT_DETAILS_PARAGRAPH, TEXT_DETAILS_LINE, TEXT_DETAILS_WORD, TEXT_DETAILS_CHARACTER, TEXT_DETAILS_ALL)]
        if py3k:
            # Representations of expression are slightly different in Python ≥ 3.0.
            def m(s):
                return s.replace(r'\xe2\x86\x92', r'→')
        else:
            def m(s):
                return s
        assert_equal(text_s_detail[0], text_s_detail[1])
        assert_equal(text_s_detail[1], text_s_detail[2])
        assert_equal(text_s_detail[2], text_s_detail[3])
        assert_equal(repr(text_s_detail[0]), m(r"""Expression((Symbol('page'), 0, 0, 2550, 3300, '5E \n5.1 E1 \n\xe2\x86\x921 \n5.2 E2 \nhttp://jwilk.net/ \n5 \n'))"""))
        assert_equal(repr(text_s_detail[4]), m(r"""Expression((Symbol('page'), 0, 0, 2550, 3300, (Symbol('line'), 462, 2726, 615, 2775, '5E '), (Symbol('line'), 462, 2544, 663, 2586, '5.1 E1 '), (Symbol('line'), 466, 2349, 631, 2421, '\xe2\x86\x921 '), (Symbol('line'), 462, 2124, 665, 2166, '5.2 E2 '), (Symbol('line'), 465, 1911, 1504, 2000, 'http://jwilk.net/ '), (Symbol('line'), 1259, 374, 1280, 409, '5 ')))"""))
        assert_true(text_s_detail[5] == text_s)
        assert_true(text_s_detail[6] == text_s)
        assert_true(text_s_detail[7] == text_s)
        assert_equal(repr(text_s), m(r"""Expression((Symbol('page'), 0, 0, 2550, 3300, (Symbol('line'), 462, 2726, 615, 2775, (Symbol('word'), 462, 2726, 615, 2775, '5E')), (Symbol('line'), 462, 2544, 663, 2586, (Symbol('word'), 462, 2544, 533, 2586, '5.1'), (Symbol('word'), 596, 2545, 663, 2586, 'E1')), (Symbol('line'), 466, 2349, 631, 2421, (Symbol('word'), 466, 2349, 631, 2421, '\xe2\x86\x921')), (Symbol('line'), 462, 2124, 665, 2166, (Symbol('word'), 462, 2124, 535, 2166, '5.2'), (Symbol('word'), 596, 2125, 665, 2166, 'E2')), (Symbol('line'), 465, 1911, 1504, 2000, (Symbol('word'), 465, 1911, 1504, 2000, 'http://jwilk.net/')), (Symbol('line'), 1259, 374, 1280, 409, (Symbol('word'), 1259, 374, 1280, 409, '5'))))"""))

        with raises(TypeError, 'details must be a symbol or none'):
            PageText(page, 'eggs')

        with raises(ValueError, 'details must be equal to TEXT_DETAILS_PAGE, or TEXT_DETAILS_COLUMN, or TEXT_DETAILS_REGION, or TEXT_DETAILS_PARAGRAPH, or TEXT_DETAILS_LINE, or TEXT_DETAILS_WORD, or TEXT_DETAILS_CHARACTER or TEXT_DETAILS_ALL'):
            PageText(page, Symbol('eggs'))

# vim:ts=4 sw=4 et
