# encoding=UTF-8

# Copyright © 2007-2016 Jakub Wilk <jwilk@jwilk.net>
#
# This file is part of python-djvulibre.
#
# python-djvulibre is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# python-djvulibre is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.

import array
import errno
import os
import shutil
import subprocess
import sys
import tempfile

from djvu.decode import (
    AffineTransform,
    Context,
    DDJVU_VERSION,
    DOCUMENT_TYPE_BUNDLED,
    DOCUMENT_TYPE_SINGLE_PAGE,
    DocInfoMessage,
    Document,
    DocumentAnnotations,
    DocumentDecodingJob,
    DocumentOutline,
    ErrorMessage,
    File,
    FileUri,
    Hyperlinks,
    Job,
    JobFailed,
    JobOK,
    Message,
    Metadata,
    NewStreamMessage,
    NotAvailable,
    PAGE_TYPE_BITONAL,
    Page,
    PageAnnotations,
    PageJob,
    PageText,
    PixelFormat,
    PixelFormatGrey,
    PixelFormatPackedBits,
    PixelFormatPalette,
    PixelFormatRgb,
    PixelFormatRgbMask,
    RENDER_COLOR,
    SaveJob,
    Stream,
    TEXT_DETAILS_ALL,
    TEXT_DETAILS_CHARACTER,
    TEXT_DETAILS_COLUMN,
    TEXT_DETAILS_LINE,
    TEXT_DETAILS_PAGE,
    TEXT_DETAILS_PARAGRAPH,
    TEXT_DETAILS_REGION,
    TEXT_DETAILS_WORD,
    ThumbnailMessage,
    __version__,
)
from djvu.sexpr import (
    Expression,
    Symbol,
)

from tools import (
    assert_equal,
    assert_false,
    assert_is,
    assert_is_instance,
    assert_list_equal,
    assert_multi_line_equal,
    assert_raises,
    assert_raises_regex,
    assert_raises_str,
    assert_repr,
    assert_true,
    SkipTest,
    skip_unless_c_messages,
    skip_unless_command_exists,
    skip_unless_translation_exists,
    interim_locale,
    locale_encoding,
    wildcard_import,
    # Python 2/3 compat:
    b,
    maxsize,
    py3k,
    u,
    unicode,
)

images = os.path.join(os.path.dirname(__file__), 'images', '')

if sys.version_info >= (3, 2):
    array_tobytes = array.array.tobytes
else:
    array_tobytes = array.array.tostring

def run(*cmd, **kwargs):
    stdin = kwargs.pop('stdin', None)
    env = {}
    for key, value in kwargs.items():
        if key.isupper():
            env[key] = value
            continue
        raise TypeError('{key!r} is an invalid keyword argument for this function'.format(key=key))
    def preexec_fn():
        os.environ.update(env)
    kwargs = dict(
        preexec_fn=preexec_fn,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if stdin is not None:
        kwargs.update(stdin=subprocess.PIPE)
    child = subprocess.Popen(list(cmd), **kwargs)
    (stdout, stderr) = child.communicate(stdin)
    if child.returncode != 0:
        raise subprocess.CalledProcessError(child.returncode, cmd[0])
    return (stdout, stderr)

def create_djvu(commands='', sexpr=''):
    skip_unless_command_exists('djvused')
    if sexpr:
        commands += '\nset-ant\n{sexpr}\n.\n'.format(sexpr=sexpr)
    file = tempfile.NamedTemporaryFile(prefix='test', suffix='djvu')
    file.seek(0)
    file.write(
        b'\x41\x54\x26\x54\x46\x4f\x52\x4d\x00\x00\x00\x22\x44\x4a\x56\x55'
        b'\x49\x4e\x46\x4f\x00\x00\x00\x0a\x00\x01\x00\x01\x18\x00\x2c\x01'
        b'\x16\x01\x53\x6a\x62\x7a\x00\x00\x00\x04\xbc\x73\x1b\xd7'
    )
    file.flush()
    (stdout, stderr) = run('djvused', '-s', file.name, stdin=commands.encode(locale_encoding))
    assert_equal(stdout, ''.encode(locale_encoding))
    assert_equal(stderr, ''.encode(locale_encoding))
    return file

def test_context_cache():
    context = Context()
    assert_equal(context.cache_size, 10 << 20)
    for n in -100, 0, 1 << 31:
        with assert_raises_str(ValueError, '0 < cache_size < (2 ** 31) must be satisfied'):
            context.cache_size = n
    with assert_raises_str(ValueError, '0 < cache_size < (2 ** 31) must be satisfied'):
        context.cache_size = 0
    n = 1
    while n < (1 << 31):
        context.cache_size = n
        assert_equal(context.cache_size, n)
        n = (n + 1) * 2 - 1
    context.clear_cache()

class test_documents:

    def test_bad_new(self):
        with assert_raises_str(TypeError, "cannot create 'djvu.decode.Document' instances"):
            Document()

    def test_nonexistent(self):
        path = '__nonexistent__'
        try:
            os.stat(path)
        except OSError:
            _, ex, _ = sys.exc_info()
            c_message = ex.args[1]
        else:
            raise OSError(errno.EEXIST, os.strerror(errno.EEXIST), path)
        c_message.encode('ASCII')
        skip_unless_c_messages()
        context = Context()
        with assert_raises(JobFailed):
            context.new_document(FileUri(path))
        message = context.get_message()
        assert_equal(type(message), ErrorMessage)
        assert_equal(type(message.message), unicode)
        assert_equal(
            message.message,
            "[1-11711] Failed to open '{path}': {msg}.".format(path=path, msg=c_message)
        )
        assert_equal(str(message), message.message)
        assert_equal(unicode(message), message.message)

    def test_nonexistent_ja(self):
        skip_unless_c_messages()
        skip_unless_translation_exists('ja_JP.UTF-8')
        path = '__nonexistent__'
        context = Context()
        try:
            with interim_locale(LC_ALL='ja_JP.UTF-8'):
                os.stat(path)
        except OSError:
            _, ex, _ = sys.exc_info()
            c_message = ex.args[1]
        else:
            raise OSError(errno.EEXIST, os.strerror(errno.EEXIST), path)
        try:
            c_message.encode('ASCII')
        except UnicodeError:
            pass
        else:
            raise AssertionError(
                'ja_JP error message is ASCII-only: {msg!r}'.format(msg=c_message)
            )
        with interim_locale(LC_ALL='ja_JP.UTF-8'):
            with assert_raises(JobFailed):
                context.new_document(FileUri(path))
            message = context.get_message()
            assert_equal(type(message), ErrorMessage)
            assert_equal(type(message.message), unicode)
            assert_equal(
                message.message,
                u("[1-11711] Failed to open '{path}': {msg}.".format(path=path, msg=c_message))
            )
            assert_equal(
                str(message),
                "[1-11711] Failed to open '{path}': {msg}.".format(path=path, msg=c_message)
            )
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
        assert_is(type(file), File)
        assert_is(file.document, document)
        assert_is(file.get_info(), None)
        assert_equal(file.type, 'P')
        assert_equal(file.n_page, 0)
        page = file.page
        assert_equal(type(page), Page)
        assert_is(page.document, document)
        assert_equal(page.n, 0)
        assert_is(file.size, None)
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
        assert_is(page.document, document)
        assert_is(page.get_info(), None)
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
        assert_is(document.get_message(wait=False), None)
        assert_is(context.get_message(wait=False), None)
        with assert_raises_str(IndexError, 'file number out of range'):
            document.files[-1].get_info()
        assert_is(document.get_message(wait=False), None)
        assert_is(context.get_message(wait=False), None)
        with assert_raises_str(IndexError, 'page number out of range'):
            document.pages[-1]
        with assert_raises_str(IndexError, 'page number out of range'):
            document.pages[1]
        assert_is(document.get_message(wait=False), None)
        assert_is(context.get_message(wait=False), None)

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
        assert_equal(len(document.pages), 2)
        assert_equal(len(document.files), 3)
        (stdout0, stderr0) = run('djvudump', original_filename, LC_ALL='C')
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
            (stdout, stderr) = run('djvudump', tmp.name, LC_ALL='C')
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
            stdout, stderr = run('djvudump', tmp.name, LC_ALL='C')
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
            (stdout, stderr) = run('djvudump', tmpfname, LC_ALL='C')
            assert_equal(stderr, b(''))
            stdout = stdout.replace(b('\r\n'), b('\n'))
            stdout = stdout.split(b('\n'))
            stdout0 = (
                [b('      shared_anno.iff -> shared_anno.iff')] +
                [b('      p{n:04}.djvu -> p{n:04}.djvu'.format(n=n)) for n in range(1, 3)]
            )
            assert_equal(len(stdout), 7)
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
            (stdout, stderr) = run('djvudump', tmpfname, LC_ALL='C')
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
        assert_equal(len(document.pages), 2)
        assert_equal(len(document.files), 3)
        tmp = tempfile.NamedTemporaryFile()
        try:
            job = document.export_ps(tmp.file)
            assert_equal(type(job), SaveJob)
            assert_true(job.is_done)
            assert_false(job.is_error)
            stdout, stderr = run('ps2ascii', tmp.name, LC_ALL='C')
            assert_equal(stderr, b(''))
            assert_equal(stdout, b('\x0c') * 2)
        finally:
            tmp.close()

        tmp = tempfile.NamedTemporaryFile()
        try:
            job = document.export_ps(tmp.file, pages=(0,), text=True)
            assert_equal(type(job), SaveJob)
            assert_true(job.is_done)
            assert_false(job.is_error)
            stdout, stderr = run('ps2ascii', tmp.name, LC_ALL='C')
            assert_equal(stderr, b(''))
            stdout = stdout.decode('ASCII')
            stdout = ' '.join(stdout.split())
            expected = '''
                1 Lorem ipsum
                Optio reprehenderit molestias amet aliquam, similique doloremque fuga labore
                voluptatum voluptatem, commodi culpa voluptas, officia tenetur expedita quidem
                hic repellat molestiae quis accusamus dolores repudiandae, quidem in ad
                voluptas eligendi maiores placeat ex consectetur at tenetur amet.
                1
            '''
            expected = ' '.join(expected.split())
            assert_multi_line_equal(stdout, expected)
        finally:
            del tmp

class test_pixel_formats():

    def test_bad_new(self):
        with assert_raises_str(TypeError, "cannot create 'djvu.decode.PixelFormat' instances"):
            PixelFormat()

    def test_rgb(self):
        pf = PixelFormatRgb()
        assert_repr(pf, "djvu.decode.PixelFormatRgb(byte_order = 'RGB', bpp = 24)")
        pf = PixelFormatRgb('RGB')
        assert_repr(pf, "djvu.decode.PixelFormatRgb(byte_order = 'RGB', bpp = 24)")
        pf = PixelFormatRgb('BGR')
        assert_repr(pf, "djvu.decode.PixelFormatRgb(byte_order = 'BGR', bpp = 24)")

    def test_rgb_mask(self):
        pf = PixelFormatRgbMask(0xff, 0xf00, 0x1f000, 0, 16)
        assert_repr(pf, "djvu.decode.PixelFormatRgbMask(red_mask = 0x00ff, green_mask = 0x0f00, blue_mask = 0xf000, xor_value = 0x0000, bpp = 16)")
        pf = PixelFormatRgbMask(0xff000000, 0xff0000, 0xff00, 0xff, 32)
        assert_repr(pf, "djvu.decode.PixelFormatRgbMask(red_mask = 0xff000000, green_mask = 0x00ff0000, blue_mask = 0x0000ff00, xor_value = 0x000000ff, bpp = 32)")

    def test_grey(self):
        pf = PixelFormatGrey()
        assert_repr(pf, "djvu.decode.PixelFormatGrey(bpp = 8)")

    def test_palette(self):
        with assert_raises(KeyError) as ecm:
            pf = PixelFormatPalette({})
        assert_equal(
            ecm.exception.args,
            ((0, 0, 0),)
        )
        data = dict(((i, j, k), i + 7 * j + 37 + k) for i in range(6) for j in range(6) for k in range(6))
        pf = PixelFormatPalette(data)
        data_repr = ', '.join(
            '{k!r}: 0x{v:02x}'.format(k=k, v=v) for k, v in sorted(data.items())
        )
        assert_equal(
            repr(pf),
            'djvu.decode.PixelFormatPalette({{{data}}}, bpp = 8)'.format(data=data_repr)
        )

    def test_packed_bits(self):
        pf = PixelFormatPackedBits('<')
        assert_repr(pf, "djvu.decode.PixelFormatPackedBits('<')")
        assert_equal(pf.bpp, 1)
        pf = PixelFormatPackedBits('>')
        assert_repr(pf, "djvu.decode.PixelFormatPackedBits('>')")
        assert_equal(pf.bpp, 1)

class test_page_jobs():

    def test_bad_new(self):
        with assert_raises_str(TypeError, "cannot create 'djvu.decode.PageJob' instances"):
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
        with assert_raises_str(ValueError, 'rotation must be equal to 0, 90, 180, or 270'):
            page_job.rotation = 100
        page_job.rotation = 180
        assert_equal((page_job.rotation, page_job.initial_rotation), (180, 0))
        del page_job.rotation
        assert_equal((page_job.rotation, page_job.initial_rotation), (0, 0))

        with assert_raises_str(ValueError, 'page_rect width/height must be a positive integer'):
            page_job.render(RENDER_COLOR, (0, 0, -1, -1), (0, 0, 10, 10), PixelFormatRgb())

        with assert_raises_str(ValueError, 'render_rect width/height must be a positive integer'):
            page_job.render(RENDER_COLOR, (0, 0, 10, 10), (0, 0, -1, -1), PixelFormatRgb())

        with assert_raises_str(ValueError, 'render_rect must be inside page_rect'):
            page_job.render(RENDER_COLOR, (0, 0, 10, 10), (2, 2, 10, 10), PixelFormatRgb())

        with assert_raises_str(ValueError, 'row_alignment must be a positive integer'):
            page_job.render(RENDER_COLOR, (0, 0, 10, 10), (0, 0, 10, 10), PixelFormatRgb(), -1)

        with assert_raises_regex(MemoryError, r'\AUnable to allocate [0-9]+ bytes for an image memory\Z'):
            x = int((maxsize//2) ** 0.5)
            page_job.render(RENDER_COLOR, (0, 0, x, x), (0, 0, x, x), PixelFormatRgb(), 8)

        s = page_job.render(RENDER_COLOR, (0, 0, 10, 10), (0, 0, 4, 4), PixelFormatGrey(), 1)
        assert_equal(s, b'\xff\xff\xff\xff\xff\xff\xff\xef\xff\xff\xff\xa4\xff\xff\xff\xb8')

        buffer = array.array('B', b'\0')
        with assert_raises_str(ValueError, 'Image buffer is too small (16 > 1)'):
            page_job.render(RENDER_COLOR, (0, 0, 10, 10), (0, 0, 4, 4), PixelFormatGrey(), 1, buffer)

        buffer = array.array('B', b'\0' * 16)
        assert_is(page_job.render(RENDER_COLOR, (0, 0, 10, 10), (0, 0, 4, 4), PixelFormatGrey(), 1, buffer), buffer)
        s = array_tobytes(buffer)
        assert_equal(s, b'\xff\xff\xff\xff\xff\xff\xff\xef\xff\xff\xff\xa4\xff\xff\xff\xb8')

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
        assert_is(pixels, None)
        (w, h, r), pixels = thumbnail.render((5, 5), PixelFormatGrey())
        assert_equal((w, h, r), (5, 3, 5))
        assert_equal(pixels[:15], b'\xff\xeb\xa7\xf2\xff\xff\xbf\x86\xbe\xff\xff\xe7\xd6\xe7\xff')
        buffer = array.array('B', b'\0')
        with assert_raises_str(ValueError, 'Image buffer is too small (25 > 1)'):
            (w, h, r), pixels = thumbnail.render((5, 5), PixelFormatGrey(), buffer=buffer)
        buffer = array.array('B', b'\0' * 25)
        (w, h, r), pixels = thumbnail.render((5, 5), PixelFormatGrey(), buffer=buffer)
        assert_is(pixels, buffer)
        s = array_tobytes(buffer[:15])
        assert_equal(s, b'\xff\xeb\xa7\xf2\xff\xff\xbf\x86\xbe\xff\xff\xe7\xd6\xe7\xff')

def test_jobs():

    with assert_raises_str(TypeError, "cannot create 'djvu.decode.Job' instances"):
        Job()

    with assert_raises_str(TypeError, "cannot create 'djvu.decode.DocumentDecodingJob' instances"):
        DocumentDecodingJob()

class test_affine_transforms():

    def test_bad_args(self):
        with assert_raises_str(ValueError, 'need more than 2 values to unpack'):
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
        with assert_raises_str(TypeError, "cannot create 'djvu.decode.Message' instances"):
            Message()

class test_streams:

    def test_bad_new(self):
        with assert_raises_str(TypeError, "Argument 'document' has incorrect type (expected djvu.decode.Document, got NoneType)"):
            Stream(None, 42)

    def test(self):
        context = Context()
        document = context.new_document('dummy://dummy.djvu')
        message = document.get_message()
        assert_equal(type(message), NewStreamMessage)
        assert_equal(message.name, 'dummy.djvu')
        assert_equal(message.uri, 'dummy://dummy.djvu')
        assert_equal(type(message.stream), Stream)
        with assert_raises(NotAvailable):
            document.outline.sexpr
        with assert_raises(NotAvailable):
            document.annotations.sexpr
        with assert_raises(NotAvailable):
            document.pages[0].text.sexpr
        with assert_raises(NotAvailable):
            document.pages[0].annotations.sexpr
        try:
            with open(images + 'test1.djvu', 'rb') as fp:
                message.stream.write(fp.read())
        finally:
            message.stream.close()
        with assert_raises_str(IOError, 'I/O operation on closed file'):
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
    meta = '\n'.join(u('|{k}| {v}').format(k=k, v=v) for k, v in model_metadata.items())
    test_script = u('set-meta\n{meta}\n.\n').format(meta=meta)
    try:
        test_file = create_djvu(test_script)
    except UnicodeEncodeError:
        raise SkipTest('you need to run this test with LC_CTYPE=C or LC_CTYPE=<lang>.UTF-8')
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
            with assert_raises(KeyError) as ecm:
                metadata[k]
            assert_equal(ecm.exception.args, (k,))
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
        assert_is(anno.background_color, None)
        assert_is(anno.horizontal_align, None)
        assert_is(anno.vertical_align, None)
        assert_is(anno.mode, None)
        assert_is(anno.zoom, None)
        expected_metadata = [
            Symbol('metadata'),
            [Symbol('ModDate'), '2015-08-17 19:54:57+02:00'],
            [Symbol('CreationDate'), '2015-08-17 19:54:57+02:00'],
            [Symbol('Producer'), 'pdfTeX-1.40.16'],
            [Symbol('Creator'), 'LaTeX with hyperref package'],
            [Symbol('Author'), 'Jakub Wilk']
        ]
        expected_xmp = [
            Symbol('xmp'),
            '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
            '<rdf:Description rdf:about="">'
                '<xmpMM:History xmlns:xmpMM="http://ns.adobe.com/xap/1.0/mm/"><rdf:Seq><rdf:li xmlns:stEvt="http://ns.adobe.com/xap/1.0/sType/ResourceEvent#" stEvt:action="converted" stEvt:parameters="from application/pdf to image/vnd.djvu" stEvt:softwareAgent="pdf2djvu 0.8.1 (DjVuLibre 3.5.27, Poppler 0.26.5, GraphicsMagick++ 1.3.21, GNOME XSLT 1.1.28, GNOME XML 2.9.2, PStreams 0.8.0)" stEvt:when="2015-08-17T17:54:58+00:00"/></rdf:Seq></xmpMM:History>'
                '<dc:creator xmlns:dc="http://purl.org/dc/elements/1.1/">Jakub Wilk</dc:creator>'
                '<dc:format xmlns:dc="http://purl.org/dc/elements/1.1/">image/vnd.djvu</dc:format>'
                '<pdf:Producer xmlns:pdf="http://ns.adobe.com/pdf/1.3/">pdfTeX-1.40.16</pdf:Producer>'
                '<xmp:CreatorTool xmlns:xmp="http://ns.adobe.com/xap/1.0/">LaTeX with hyperref package</xmp:CreatorTool>'
                '<xmp:CreateDate xmlns:xmp="http://ns.adobe.com/xap/1.0/">2015-08-17T19:54:57+02:00</xmp:CreateDate>'
                '<xmp:ModifyDate xmlns:xmp="http://ns.adobe.com/xap/1.0/">2015-08-17T19:54:57+02:00</xmp:ModifyDate>'
                '<xmp:MetadataDate xmlns:xmp="http://ns.adobe.com/xap/1.0/">2015-08-17T17:54:58+00:00</xmp:MetadataDate>'
            '</rdf:Description>'
            '</rdf:RDF>\n'
        ]
        assert_equal(
            anno.sexpr,
            Expression([expected_metadata, expected_xmp])
        )
        metadata = anno.metadata
        assert_equal(type(metadata), Metadata)
        hyperlinks = anno.hyperlinks
        assert_equal(type(hyperlinks), Hyperlinks)
        assert_equal(len(hyperlinks), 0)
        assert_equal(list(hyperlinks), [])
        outline = document.outline
        assert_equal(type(outline), DocumentOutline)
        outline.wait()
        assert_equal(outline.sexpr, Expression(
            [Symbol('bookmarks'),
                ['Lorem ipsum', '#p0001.djvu'],
                ['Hyperlinks', '#p0002.djvu',
                    ['local', '#p0002.djvu'],
                    ['remote', '#p0002.djvu']
                ]
            ]
        ))
        page = document.pages[1]
        anno = page.annotations
        assert_equal(type(anno), PageAnnotations)
        anno.wait()
        assert_is(anno.background_color, None)
        assert_is(anno.horizontal_align, None)
        assert_is(anno.vertical_align, None)
        assert_is(anno.mode, None)
        assert_is(anno.zoom, None)
        expected_hyperlinks = [
            [Symbol('maparea'), '#p0001.djvu', '', [Symbol('rect'), 520, 2502, 33, 42], [Symbol('border'), Symbol('#ff0000')]],
            [Symbol('maparea'), 'http://jwilk.net/', '', [Symbol('rect'), 458, 2253, 516, 49], [Symbol('border'), Symbol('#00ffff')]]
        ]
        assert_equal(
            anno.sexpr,
            Expression([expected_metadata, expected_xmp] + expected_hyperlinks)
        )
        page_metadata = anno.metadata
        assert_equal(type(page_metadata), Metadata)
        assert_equal(page_metadata.keys(), metadata.keys())
        assert_equal([page_metadata[k] == metadata[k] for k in metadata], [True, True, True, True, True])
        hyperlinks = anno.hyperlinks
        assert_equal(type(hyperlinks), Hyperlinks)
        assert_equal(len(hyperlinks), 2)
        assert_equal(
            list(hyperlinks),
            [Expression(h) for h in expected_hyperlinks]
        )
        text = page.text
        assert_equal(type(text), PageText)
        text.wait()
        text_s = text.sexpr
        text_s_detail = [PageText(page, details).sexpr for details in (TEXT_DETAILS_PAGE, TEXT_DETAILS_COLUMN, TEXT_DETAILS_REGION, TEXT_DETAILS_PARAGRAPH, TEXT_DETAILS_LINE, TEXT_DETAILS_WORD, TEXT_DETAILS_CHARACTER, TEXT_DETAILS_ALL)]
        assert_equal(text_s_detail[0], text_s_detail[1])
        assert_equal(text_s_detail[1], text_s_detail[2])
        assert_equal(text_s_detail[2], text_s_detail[3])
        assert_equal(
            text_s_detail[0],
            Expression(
                [Symbol('page'), 0, 0, 2550, 3300,
                    '2 Hyperlinks \n'
                    '2.1 local \n'
                    + u('→1 \n') +
                    '2.2 remote \nhttp://jwilk.net/ \n'
                    '2 \n'
                ]
            )
        )
        assert_equal(
            text_s_detail[4],
            Expression(
                [Symbol('page'), 0, 0, 2550, 3300,
                    [Symbol('line'), 462, 2712, 910, 2777, '2 Hyperlinks '],
                    [Symbol('line'), 462, 2599, 714, 2641, '2.1 local '],
                    [Symbol('line'), 464, 2505, 544, 2540, u('→1 ')],
                    [Symbol('line'), 462, 2358, 772, 2400, '2.2 remote '],
                    [Symbol('line'), 463, 2256, 964, 2298, 'http://jwilk.net/ '],
                    [Symbol('line'), 1260, 375, 1282, 409, '2 ']
                ]
            )
        )
        assert_equal(text_s_detail[5], text_s)
        assert_equal(text_s_detail[6], text_s)
        assert_equal(text_s_detail[7], text_s)
        assert_equal(
            text_s,
            Expression(
                [Symbol('page'), 0, 0, 2550, 3300,
                    [Symbol('line'), 462, 2712, 910, 2777, [Symbol('word'), 462, 2727, 495, 2776, '2'], [Symbol('word'), 571, 2712, 910, 2777, 'Hyperlinks']],
                    [Symbol('line'), 462, 2599, 714, 2641, [Symbol('word'), 462, 2599, 532, 2641, '2.1'], [Symbol('word'), 597, 2599, 714, 2640, 'local']],
                    [Symbol('line'), 464, 2505, 544, 2540, [Symbol('word'), 464, 2505, 544, 2540, u('→1')]],
                    [Symbol('line'), 462, 2358, 772, 2400, [Symbol('word'), 462, 2358, 535, 2400, '2.2'], [Symbol('word'), 598, 2358, 772, 2397, 'remote']],
                    [Symbol('line'), 463, 2256, 964, 2298, [Symbol('word'), 463, 2256, 964, 2298, 'http://jwilk.net/']],
                    [Symbol('line'), 1260, 375, 1282, 409, [Symbol('word'), 1260, 375, 1282, 409, '2']]
                ]
            )
        )
        with assert_raises_str(TypeError, 'details must be a symbol or none'):
            PageText(page, 'eggs')
        with assert_raises_str(ValueError, 'details must be equal to TEXT_DETAILS_PAGE, or TEXT_DETAILS_COLUMN, or TEXT_DETAILS_REGION, or TEXT_DETAILS_PARAGRAPH, or TEXT_DETAILS_LINE, or TEXT_DETAILS_WORD, or TEXT_DETAILS_CHARACTER or TEXT_DETAILS_ALL'):
            PageText(page, Symbol('eggs'))

def test_version():
    assert_is_instance(__version__, str)
    assert_is_instance(DDJVU_VERSION, int)

def test_wildcard_import():
    ns = wildcard_import('djvu.decode')
    assert_list_equal(
        sorted(ns.keys()), [
            'AffineTransform',
            'Annotations',
            'ChunkMessage',
            'Context',
            'DDJVU_VERSION',
            'DOCUMENT_TYPE_BUNDLED',
            'DOCUMENT_TYPE_INDIRECT',
            'DOCUMENT_TYPE_OLD_BUNDLED',
            'DOCUMENT_TYPE_OLD_INDEXED',
            'DOCUMENT_TYPE_SINGLE_PAGE',
            'DOCUMENT_TYPE_UNKNOWN',
            'DocInfoMessage',
            'Document',
            'DocumentAnnotations',
            'DocumentDecodingJob',
            'DocumentExtension',
            'DocumentFiles',
            'DocumentOutline',
            'DocumentPages',
            'ErrorMessage',
            'FILE_TYPE_INCLUDE',
            'FILE_TYPE_PAGE',
            'FILE_TYPE_THUMBNAILS',
            'File',
            'FileURI',
            'FileUri',
            'Hyperlinks',
            'InfoMessage',
            'Job',
            'JobDone',
            'JobException',
            'JobFailed',
            'JobNotDone',
            'JobNotStarted',
            'JobOK',
            'JobStarted',
            'JobStopped',
            'Message',
            'Metadata',
            'NewStreamMessage',
            'NotAvailable',
            'PAGE_TYPE_BITONAL',
            'PAGE_TYPE_COMPOUND',
            'PAGE_TYPE_PHOTO',
            'PAGE_TYPE_UNKNOWN',
            'PRINT_BOOKLET_NO',
            'PRINT_BOOKLET_RECTO',
            'PRINT_BOOKLET_VERSO',
            'PRINT_BOOKLET_YES',
            'PRINT_ORIENTATION_AUTO',
            'PRINT_ORIENTATION_LANDSCAPE',
            'PRINT_ORIENTATION_PORTRAIT',
            'Page',
            'PageAnnotations',
            'PageInfoMessage',
            'PageJob',
            'PageText',
            'PixelFormat',
            'PixelFormatGrey',
            'PixelFormatPackedBits',
            'PixelFormatPalette',
            'PixelFormatRgb',
            'PixelFormatRgbMask',
            'ProgressMessage',
            'RENDER_BACKGROUND',
            'RENDER_BLACK',
            'RENDER_COLOR',
            'RENDER_COLOR_ONLY',
            'RENDER_FOREGROUND',
            'RENDER_MASK_ONLY',
            'RedisplayMessage',
            'RelayoutMessage',
            'SaveJob',
            'Stream',
            'TEXT_DETAILS_ALL',
            'TEXT_DETAILS_CHARACTER',
            'TEXT_DETAILS_COLUMN',
            'TEXT_DETAILS_LINE',
            'TEXT_DETAILS_PAGE',
            'TEXT_DETAILS_PARAGRAPH',
            'TEXT_DETAILS_REGION',
            'TEXT_DETAILS_WORD',
            'Thumbnail',
            'ThumbnailMessage',
            'cmp_text_zone'
        ]
    )

# vim:ts=4 sts=4 sw=4 et
