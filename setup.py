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

'''
*python-djvulibre* is a set of `Python <http://python.org>`_ bindings for the
`DjVuLibre <http://djvu.sf.net/>`_ library, an open source implementation of
`DjVu <http://djvu.org/>`_.
'''

classifiers = '''
Development Status :: 4 - Beta
Intended Audience :: Developers
License :: OSI Approved :: GNU General Public License (GPL)
Operating System :: POSIX
Programming Language :: Python
Programming Language :: Python :: 2
Programming Language :: Python :: 3
Topic :: Multimedia :: Graphics
Topic :: Multimedia :: Graphics :: Graphics Conversion
Topic :: Text Processing
'''.strip().split('\n')

import glob
import os
import sys
import distutils
import subprocess as ipc

cython_needed = not os.getenv('python_djvulibre_no_cython')

def ext_modules():
    for pyx_file in glob.glob(os.path.join('djvu', '*.pyx')):
        module, _ = os.path.splitext(os.path.basename(pyx_file))
        yield module
ext_modules = list(ext_modules())
ext_extension = 'pyx' if cython_needed else 'c'

if cython_needed:
    import Cython.Distutils as distutils_build_ext
    # This is required to make setuptools cooperate with Cython
    # (well, at least with some older Cython/setuptools combinations):
    fake_module = type(sys)('fake_module')
    fake_module.build_ext = None
    sys.modules['Pyrex'] = sys.modules['Pyrex.Distutils'] = sys.modules['Pyrex.Distutils.build_ext'] = fake_module

try:
    from setuptools import setup
    from setuptools.extension import Extension
except ImportError:
    from distutils.core import setup
    from distutils.extension import Extension, have_pyrex
    assert have_pyrex
    del have_pyrex
from distutils.ccompiler import get_default_compiler

if not cython_needed:
    import distutils.command.build_ext as distutils_build_ext

def get_version():
    changelog = open(os.path.join('doc', 'changelog'))
    try:
        return changelog.readline().split()[1].strip('()')
    finally:
        changelog.close()

PKG_CONFIG_FLAG_MAP = {'-I': 'include_dirs', '-L': 'library_dirs', '-l': 'libraries'}

def pkg_config(*packages, **kwargs):
    pkgconfig = ipc.Popen(
        ['pkg-config', '--libs', '--cflags'] + list(packages),
        stdout=ipc.PIPE, stderr=ipc.PIPE
    )
    stdout, stderr = pkgconfig.communicate()
    stdout = stdout.decode('ASCII', 'replace')
    stderr = stderr.decode('ASCII', 'replace')
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
        path = os.path.join(r'C:\Program Files', 'DjVuZone', 'DjVuLibre')
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

os.putenv('TAR_OPTIONS', '--owner root --group root --mode a+rX')

class build_ext(distutils_build_ext.build_ext):

    def run(self):
        filename = 'djvu/config.pxi'
        distutils.log.info('creating %r' % filename)
        distutils.file_util.write_file(filename, [
            'DEF PY3K = %d' % (sys.version_info >= (3, 0)),
            'DEF PYTHON_DJVULIBRE_VERSION = "%s"' % __version__,
        ])
        distutils.command.build_ext.build_ext.run(self)

setup_params = dict(
    name = 'python-djvulibre',
    version = __version__,
    author = 'Jakub Wilk',
    author_email = 'jwilk@jwilk.net',
    license = 'GNU GPL 2',
    description = 'Python support for the DjVu image format',
    long_description = __doc__.strip(),
    classifiers = classifiers,
    url = 'http://jwilk.net/software/python-djvulibre',
    platforms = ['all'],
    packages = ['djvu'],
    ext_modules = [
        Extension(
            'djvu.%s' % name, ['djvu/%s.%s' % (name, ext_extension)],
            **pkg_config('ddjvuapi')
        )
        for name in ext_modules
    ],
    py_modules = ['djvu.const'],
    cmdclass = dict(build_ext = build_ext)
)

if __name__ == '__main__':
    setup(**setup_params)

# vim:ts=4 sw=4 et
