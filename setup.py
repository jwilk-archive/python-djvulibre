# encoding=UTF-8
# Copyright © 2007, 2008, 2009 Jakub Wilk <ubanus@users.sf.net>

'''
*python-djvulibre* is a set of `Python <http://python.org>`_ bindings for the
`DjVuLibre <http://djvu.sf.net/>`_ library, an open source implementation of
`DjVu <http://djvu.org/>`_.
'''

classifiers = '''\
Development Status :: 4 - Beta
Intended Audience :: Developers
License :: OSI Approved :: GNU General Public License (GPL)
Operating System :: POSIX
Programming Language :: Python
Programming Language :: Python :: 2
Topic :: Multimedia :: Graphics
Topic :: Multimedia :: Graphics :: Graphics Conversion
Topic :: Text Processing\
'''.split('\n')

import os
import sys

from Cython.Distutils import build_ext

# This is required to make setuptools cooperate with Cython:
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'fake_pyrex'))
try:
    from setuptools import setup
    from setuptools.extension import Extension
except ImportError:
    from distutils.core import setup
    from distutils.extension import Extension
from distutils.ccompiler import get_default_compiler

from subprocess import Popen, PIPE

EXT_MODULES = ('decode', 'sexpr')

def get_version():
    import os.path
    from re import match
    package_dir = os.path.dirname(os.path.realpath(os.path.splitext(__file__)[0] + '.py'))
    changelog = file(os.path.join(package_dir, 'doc/changelog'))
    try:
        line = changelog.readline()
        m = match('python-djvulibre [(]([0-9.]+)[)]', line)
        return m.group(1)
    finally:
        changelog.close()

PKG_CONFIG_FLAG_MAP = {'-I': 'include_dirs', '-L': 'library_dirs', '-l': 'libraries'}

def pkg_config(*packages, **kwargs):
    pkgconfig = Popen(
        ['pkg-config', '--libs', '--cflags'] + list(packages),
        stdout = PIPE, stderr = PIPE
    )
    stdout, stderr = pkgconfig.communicate()
    if pkgconfig.returncode:
        raise IOError('[pkg-config] ' + stderr.strip())
    kwargs.setdefault('extra_link_args', [])
    kwargs.setdefault('extra_compile_args', ['-Wno-uninitialized'])
    for argument in stdout.split():
        key = argument[:2]
        try:
            value = argument[2:]
            kwargs.setdefault(PKG_CONFIG_FLAG_MAP[key], []).append(value)
        except KeyError:
            kwargs['extra_link_args'].append(argument)
            kwargs['extra_compile_args'].append(argument)
    return kwargs

if get_default_compiler() == 'msvc':

    # Hack to be enable building python-djvulibre with Microsoft Visual C++
    # compiler follows.
    #
    # Note that all of these needs to be compiled with *the same* compiler:
    # - Python,
    # - DjVuLibre,
    # - python-djvulibre.
    #
    # Fortunately, pre-compiled binaries of both Python 2.6 and DjVuLibre
    # 3.5.22 were compiled with Microsoft Visual C++ 9.0.

    def get_djvulibre_path():
        path = os.path.join(os.getenv('') or r'C:\Program Files', 'DjVuZone', 'DjVuLibre')
        for ext in 'lib', 'dll':
            if not os.path.exists(os.path.join(path, 'libdjvulibre.' + ext)):
                raise RuntimeError('DjVuLibre library not found')
        return path

    def pkg_config(*packages, **kwargs):
        library_dirs = kwargs.setdefault('library_dirs', [])
        include_dirs = kwargs.setdefault('include_dirs', [])
        libraries = kwargs.setdefault('libraries', [])
        macros = kwargs.setdefault('define_macros', [])
        macros[:] = [(key, value.replace('"', r'\"')) for key, value in macros]
        djvulibre_path = get_djvulibre_path()
        for dirs in include_dirs, library_dirs:
            dirs.append(djvulibre_path)
        libraries.append('libdjvulibre')
        macros.append(('inline', ''))
        macros.append(('WIN32', '1'))
        return kwargs

__version__ = get_version()

setup_params = dict(
    name = 'python-djvulibre',
    version = __version__,
    author = 'Jakub Wilk',
    author_email = 'ubanus@users.sf.net',
    license = 'GNU GPL 2',
    description = 'Python support for the DjVu image format',
    long_description = __doc__.strip(),
    classifiers = classifiers,
    url = 'http://jwilk.net/software/python-djvulibre.html',
    platforms = ['all'],
    packages = ['djvu'],
    ext_modules = \
    [
        Extension(
            'djvu.%s' % name, ['djvu/%s.pyx' % name],
            **pkg_config(
                'ddjvuapi',
                define_macros = [('PYTHON_DJVULIBRE_VERSION', '"%s"' % __version__)]
            )
        )
        for name in EXT_MODULES
    ],
    py_modules = ['djvu.const'],
    cmdclass = dict(build_ext = build_ext)
)

if __name__ == '__main__':
    setup(**setup_params)

# vim:ts=4 sw=4 et
