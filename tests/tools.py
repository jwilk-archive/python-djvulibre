# encoding=UTF-8

# Copyright © 2010-2015 Jakub Wilk <jwilk@jwilk.net>
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
import locale
import os
import re
import sys

from nose import SkipTest

import nose.tools

from nose.tools import (
    assert_true,
    assert_false,
    assert_equal,
    assert_not_equal,
)

def noseimport(vmaj, vmin, name=None):
    def wrapper(f):
        if f.__module__ == 'unittest.case':
            return f
        if sys.version_info >= (vmaj, vmin):
            return getattr(nose.tools, name or f.__name__)
        return f
    return wrapper

@noseimport(2, 7)
def assert_in(x, y):
    assert_true(
        x in y,
        msg='{0!r} not found in {1!r}'.format(x, y)
    )

@noseimport(2, 7)
def assert_is(x, y):
    assert_true(
        x is y,
        msg='{0!r} is not {1!r}'.format(x, y)
    )

@noseimport(2, 7)
def assert_is_instance(obj, cls):
    assert_true(
        isinstance(obj, cls),
        msg='{0!r} is not an instance of {1!r}'.format(obj, cls)
    )

@noseimport(2, 7)
def assert_less(x, y):
    assert_true(
        x < y,
        msg='{0!r} not less than {1!r}'.format(x, y)
    )

@noseimport(2, 7)
def assert_list_equal(x, y):
    assert_is_instance(x, list)
    assert_is_instance(y, list)
    return assert_equal(x, y)

@noseimport(2, 7)
def assert_multi_line_equal(x, y):
    return assert_equal(x, y)
if sys.version_info >= (2, 7):
    type(assert_multi_line_equal.__self__).maxDiff = None

@noseimport(2, 7)
def assert_not_in(x, y):
    assert_true(
        x not in y,
        msg='{0!r} unexpectedly found in {1!r}'.format(x, y)
    )

@noseimport(2, 7)
class assert_raises(object):
    def __init__(self, exc_type):
        self._exc_type = exc_type
        self.exception = None
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_value, tb):
        if exc_type is None:
            assert_true(False, '{0} not raised'.format(self._exc_type.__name__))
        if not issubclass(exc_type, self._exc_type):
            return False
        if isinstance(exc_value, exc_type):
            pass
            # This branch is not always taken in Python 2.6:
            # https://bugs.python.org/issue7853
        elif isinstance(exc_value, tuple):
            exc_value = exc_type(*exc_value)
        else:
            exc_value = exc_type(exc_value)
        self.exception = exc_value
        return True

@noseimport(2, 7, 'assert_raises_regexp')
@noseimport(3, 2)
@contextlib.contextmanager
def assert_raises_regex(exc_type, regex):
    with assert_raises(exc_type) as ecm:
        yield
    assert_regex(str(ecm.exception), regex)

@noseimport(2, 7, 'assert_regexp_matches')
@noseimport(3, 2)
def assert_regex(text, regex):
    if isinstance(regex, basestring):
        regex = re.compile(regex)
    if not regex.search(text):
        message = "Regex didn't match: {0!r} not found in {1!r}".format(regex.pattern, text)
        assert_true(False, msg=message)

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

py3k = sys.version_info >= (3, 0)

if py3k:
    def u(s):
        return s
else:
    def u(s):
        return s.decode('UTF-8')

if py3k:
    def b(s):
        return s.encode('UTF-8')
else:
    def b(s):
        return s

if py3k:
    long = int
else:
    long = long

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

if py3k:
    unicode = str
else:
    unicode = unicode

if py3k:
    maxsize = sys.maxsize
else:
    maxsize = sys.maxint

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
            except locale.Error:
                _, exc, _ = sys.exc_info()
                raise SkipTest(exc)
        yield
    finally:
        locale.setlocale(locale.LC_ALL, old_locale)

def assert_repr(self, expected):
    return assert_equal(repr(self), expected)

def skip_unless_c_messages():
    if locale.setlocale(locale.LC_MESSAGES) != 'C':
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
            except EnvironmentError:
                _, exc, _ = sys.exc_info()
                messages[lang] = str(exc)
    messages = set(messages.values())
    assert 1 <= len(messages) <= 2
    if len(messages) == 1:
        raise SkipTest('libc translation not found: ' + lang)

def skip_unless_command_exists(command):
    directories = os.environ['PATH'].split(os.pathsep)
    for directory in directories:
        path = os.path.join(directory, command)
        if os.access(path, os.X_OK):
            return
    raise SkipTest('command not found: ' + command)

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
    'maxsize',
    'py3k',
    'u',
    'unicode',
    # nose
    'SkipTest',
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
    'assert_regex',
    'assert_true',
    # misc
    'assert_raises_str',
    'assert_repr',
    'interim',
    'interim_locale',
    'locale_encoding',
    'skip_unless_c_messages',
    'skip_unless_command_exists',
    'skip_unless_translation_exists',
    'wildcard_import',
]

# vim:ts=4 sts=4 sw=4 et
