# encoding=UTF-8
# Copyright © 2007, 2008, 2009, 2010, 2011 Jakub Wilk <jwilk@jwilk.net>
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
Operating System :: Microsoft :: Windows :: Windows 95/98/2000
Operating System :: Microsoft :: Windows :: Windows NT/2000
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
import subprocess as ipc

if os.name == 'posix' and os.getenv('python_djvulibre_mingw32'):
    import mingw32cross
else:
    mingw32cross = None

# Just to make sure setuptools won't try to be clever:
fake_module = type(sys)('fake_module')
fake_module.build_ext = None
sys.modules['Pyrex'] = sys.modules['Pyrex.Distutils'] = sys.modules['Pyrex.Distutils.build_ext'] = fake_module
del fake_module

try:
    import setuptools as distutils_core
    import setuptools.extension
    assert setuptools.extension.have_pyrex
except ImportError:
    import distutils.core as distutils_core
import distutils
import distutils.ccompiler
import distutils.command.clean
import distutils.command.build_ext
import distutils.dep_util

try:
    import sphinx.setup_command as sphinx_setup_command
except ImportError:
    sphinx_setup_command = None

def ext_modules():
    for pyx_file in glob.glob(os.path.join('djvu', '*.pyx')):
        module, _ = os.path.splitext(os.path.basename(pyx_file))
        yield module
ext_modules = list(ext_modules())

def get_version():
    if sys.version_info >= (3, 0):
        extra = dict(encoding='UTF-8')
    else:
        extra = {}
    changelog = open(os.path.join(os.path.dirname(__file__), 'doc', 'changelog'), **extra)
    try:
        return changelog.readline().split()[1].strip('()')
    finally:
        changelog.close()

PKG_CONFIG_FLAG_MAP = {'-I': 'include_dirs', '-L': 'library_dirs', '-l': 'libraries'}

def pkg_config(*packages, **kwargs):
    try:
        pkgconfig = ipc.Popen(
            ['pkg-config', '--libs', '--cflags'] + list(packages),
            stdout=ipc.PIPE, stderr=ipc.PIPE
        )
    except OSError:
        _, ex, _ = sys.exc_info()
        ex.strerror = 'pkg-config: ' + ex.strerror
        raise
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

if mingw32cross:

    def pkg_config(*packages, **kwargs):
        return dict(
            libraries=['libdjvulibre'],
        )
        return kwargs

__version__ = get_version()

# Work-around for <http://bugs.python.org/issue969718>:
try:
    del os.environ['CFLAGS']
except KeyError:
    pass

class build_ext(distutils.command.build_ext.build_ext):

    config_filename = 'djvu/config.pxi'

    def run(self):
        new_config = [
            'DEF PY3K = %d' % (sys.version_info >= (3, 0)),
            'DEF PYTHON_DJVULIBRE_VERSION = "%s"' % __version__,
            'DEF HAVE_LANGINFO_H = %d' % (os.name == 'posix' and not mingw32cross),
        ]
        try:
            old_config = open(self.config_filename, 'rt').read()
        except IOError:
            old_config = ''
        if '\n'.join(new_config).strip() != old_config.strip():
            distutils.log.info('creating %r' % self.config_filename)
            distutils.file_util.write_file(self.config_filename, new_config)
        distutils.command.build_ext.build_ext.run(self)

    def build_extensions(self):
        self.check_extensions_list(self.extensions)
        for ext in self.extensions:
            ext.sources = list(self.cython_sources(ext))
            self.build_extension(ext)

    def cython_sources(self, ext):
        targets = {}
        deps = []
        for source in ext.sources:
            assert source.endswith('.pyx')
            target = '%s.c' % source[:-4]
            yield target
            depends = [source, self.config_filename] + ext.depends
            if not (self.force or distutils.dep_util.newer_group(depends, target)):
                distutils.log.debug('not cythoning %r (up-to-date)', ext.name)
                continue
            distutils.log.info('cythoning %r extension', ext.name)
            def build_c(source, target):
                distutils.spawn.spawn(['cython', source])
                # XXX This is needed to work around <http://bugs.debian.org/607112>.
                # Fortunately, python-djvulibre doesn't really need __Pyx_GetVtable().
                distutils.spawn.spawn(['sed', '-i~', '-e',
                    r's/\(static int __Pyx_GetVtable(PyObject [*]dict, void [*]vtabptr) {\)/\1 return 0;/',
                    target
                ])
            self.make_file(depends, target, build_c, [source, target])

class clean(distutils.command.clean.clean):

    def run(self):
        if self.all:
            for wildcard in 'djvu/*.c', 'djvu/*.c~', 'djvu/config.pxi':
                filenames = glob.glob(wildcard)
                if filenames:
                    distutils.log.info('removing %r', wildcard)
                if self.dry_run:
                    continue
                for filename in glob.glob(wildcard):
                    os.remove(filename)
        return distutils.command.clean.clean.run(self)

if sphinx_setup_command:
    class build_sphinx(sphinx_setup_command.BuildDoc):
        def run(self):
            # Make sure that djvu module is imported from the correct
            # directory.
            #
            # The current directory (which is normally in sys.path[0]) is
            # typically a wrong choice: it contains djvu/__init__.py but not
            # the extension modules. Prepend the directory that build_ext would
            # use instead.
            build_ext = self.get_finalized_command('build_ext')
            sys.path[:0] = [build_ext.build_lib]
            import djvu
            del sys.path[0]
            sphinx_setup_command.BuildDoc.run(self)
else:
    build_sphinx = None

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
        distutils.command.build_ext.Extension(
            'djvu.%s' % name, ['djvu/%s.pyx' % name],
            depends = ['djvu/common.pxi'] + glob.glob('djvu/*.pxd'),
            **pkg_config('ddjvuapi')
        )
        for name in ext_modules
    ],
    py_modules = ['djvu.const'],
    cmdclass = dict(
        (cmd.__name__, cmd)
        for cmd in (build_ext, clean, build_sphinx)
        if cmd is not None
    )
)

if __name__ == '__main__':
    distutils_core.setup(**setup_params)

# vim:ts=4 sw=4 et
