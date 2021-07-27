# encoding=UTF-8

# Copyright © 2010-2021 Jakub Wilk <jwilk@jwilk.net>
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

import codecs
import contextlib
import distutils.spawn
import io
import locale
import os
import sys
import unittest

py3k = sys.version_info >= (3, 0)

SkipTest = unittest.SkipTest

def get_changelog_version():
    here = os.path.dirname(__file__)
    path = os.path.join(here, '../doc/changelog')
    with io.open(path, encoding='UTF-8') as file:
        line = file.readline()
    return line.split()[1].strip('()')

tc = unittest.TestCase('__hash__')

assert_true = tc.assertTrue

assert_false = tc.assertFalse

assert_equal = tc.assertEqual

assert_not_equal = tc.assertNotEqual

assert_in = tc.assertIn

assert_is = tc.assertIs

assert_is_instance = tc.assertIsInstance

assert_less = tc.assertLess

assert_list_equal = tc.assertListEqual

assert_multi_line_equal = tc.assertMultiLineEqual
assert_multi_line_equal.__self__.maxDiff = None

assert_not_in = tc.assertNotIn

assert_raises = tc.assertRaises

assert_raises_regex = tc.assertRaisesRegex if py3k else tc.assertRaisesRegexp

@contextlib.contextmanager
def assert_raises_str(exc_type, s):
    with assert_raises(exc_type) as ecm:
        yield
    assert_equal(str(ecm.exception), s)

try:
    locale.LC_MESSAGES
except AttributeError:
    # A non-POSIX system.
    locale.LC_MESSAGES = locale.LC_ALL

locale_encoding = locale.getpreferredencoding()
if codecs.lookup(locale_encoding) == codecs.lookup('US-ASCII'):
    locale_encoding = 'UTF-8'

if py3k:
    u = str
else:
    def u(s):
        return s.decode('UTF-8')

if py3k:
    def b(s):
        return s.encode('UTF-8')
else:
    b = bytes

long = type(1 << 999)

if py3k:
    def cmp(x, y):
        if x == y:
            return 0
        if x < y:
            return -1
        if x > y:
            return 1
        assert False
else:
    cmp = cmp

if py3k:
    from io import StringIO
else:
    from io import BytesIO as StringIO

unicode = type(u(''))

@contextlib.contextmanager
def interim(obj, **override):
    copy = dict((key, getattr(obj, key)) for key in override)
    for key, value in override.items():
        setattr(obj, key, value)
    try:
        yield
    finally:
        for key, value in copy.items():
            setattr(obj, key, value)

@contextlib.contextmanager
def interim_locale(**kwargs):
    old_locale = locale.setlocale(locale.LC_ALL)
    try:
        for category, value in kwargs.items():
            category = getattr(locale, category)
            try:
                locale.setlocale(category, value)
            except locale.Error as exc:
                raise SkipTest(exc)
        yield
    finally:
        locale.setlocale(locale.LC_ALL, old_locale)

def assert_repr(self, expected):
    return assert_equal(repr(self), expected)

def skip_unless_c_messages():
    if locale.setlocale(locale.LC_MESSAGES) not in ('C', 'POSIX'):
        raise SkipTest('you need to run this test with LC_MESSAGES=C')
    if os.getenv('LANGUAGE', '') != '':
        raise SkipTest('you need to run this test with LANGUAGE unset')

def skip_unless_translation_exists(lang):
    messages = {}
    langs = ['C', lang]
    for lang in langs:
        with interim_locale(LC_ALL=lang):
            try:
                open(__file__ + '/')
            except EnvironmentError as exc:
                messages[lang] = str(exc)
    messages = set(messages.values())
    assert 1 <= len(messages) <= 2
    if len(messages) == 1:
        raise SkipTest('libc translation not found: ' + lang)

def skip_unless_command_exists(command):
    if distutils.spawn.find_executable(command):
        return
    raise SkipTest('command not found: ' + command)

class TestCase(unittest.TestCase):
    def __str__(self):
        return '{cls}.{name}'.format(
            cls=unittest.util.strclass(self.__class__),
            name=self._testMethodName,
        )

def testcase(f):
    class TestCase(unittest.TestCase):
        def test(self):
            return f()
        def __str__(self):
            return '{f.__module__}.{f.__name__}'.format(f=f)
    return TestCase

def wildcard_import(mod):
    ns = {}
    exec('from {mod} import *'.format(mod=mod), {}, ns)
    return ns

__all__ = [
    # Python 2/3 compat:
    'StringIO',
    'b',
    'cmp',
    'long',
    'py3k',
    'u',
    'unicode',
    # unittest(-like)
    'SkipTest',
    'TestCase',
    'testcase',
    # nose-compatible
    'assert_equal',
    'assert_false',
    'assert_in',
    'assert_is',
    'assert_is_instance',
    'assert_less',
    'assert_list_equal',
    'assert_multi_line_equal',
    'assert_not_equal',
    'assert_not_in',
    'assert_raises',
    'assert_raises_regex',
    'assert_true',
    # misc
    'assert_raises_str',
    'assert_repr',
    'get_changelog_version',
    'interim',
    'interim_locale',
    'locale_encoding',
    'skip_unless_c_messages',
    'skip_unless_command_exists',
    'skip_unless_translation_exists',
    'wildcard_import',
]

# vim:ts=4 sts=4 sw=4 et
