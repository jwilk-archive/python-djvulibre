# encoding=UTF-8

# Copyright © 2007-2015 Jakub Wilk <jwilk@jwilk.net>
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
*python-djvulibre* is a set of `Python <https://www.python.org>`_ bindings for
the `DjVuLibre <http://djvu.sf.net/>`_ library, an open source implementation
of `DjVu <http://djvu.org/>`_.
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
'''.strip().splitlines()

import glob
import os
import re
import sys
import subprocess as ipc

if os.name == 'posix' and os.getenv('python_djvulibre_mingw32'):
    import mingw32cross
else:
    mingw32cross = None

if os.name == 'nt':
    import djvu.dllpath

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
import distutils.version

try:
    import sphinx.setup_command as sphinx_setup_command
except ImportError:
    sphinx_setup_command = None

if sys.version_info < (2, 6):
    raise RuntimeError('Python >= 2.6 is required')

def ext_modules():
    for pyx_file in glob.iglob(os.path.join('djvu', '*.pyx')):
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

def pkgconfig_build_flags(*packages, **kwargs):
    flag_map = {
        '-I': 'include_dirs',
        '-L': 'library_dirs',
        '-l': 'libraries',
    }
    fallback = dict(
        libraries=['djvulibre'],
    )
    if os.name == 'nt':
        dll_path = djvu.dllpath.guess_dll_path()
        if dll_path is not None:
            fallback.update(
                extra_compile_args=['-I' + os.path.join(dll_path, 'include')],
                extra_link_args=['-L' + os.path.join(dll_path)],
            )
    try:
        pkgconfig = ipc.Popen(
            ['pkg-config', '--libs', '--cflags'] + list(packages),
            stdout=ipc.PIPE, stderr=ipc.PIPE
        )
    except OSError:
        _, ex, _ = sys.exc_info()
        distutils.log.warn('cannot execute pkg-config: ' + str(ex))
        return fallback
    stdout, stderr = pkgconfig.communicate()
    stdout = stdout.decode('ASCII', 'replace')
    stderr = stderr.decode('ASCII', 'replace')
    if pkgconfig.returncode:
        distutils.log.warn('pkg-config failed: ' + stderr.strip())
        return fallback
    kwargs.setdefault('extra_link_args', [])
    kwargs.setdefault('extra_compile_args', ['-Wno-uninitialized'])
    for argument in stdout.split():
        key = argument[:2]
        try:
            value = argument[2:]
            kwargs.setdefault(flag_map[key], []).append(value)
        except KeyError:
            kwargs['extra_link_args'].append(argument)
            kwargs['extra_compile_args'].append(argument)
    return kwargs

def pkgconfig_version(package):
    V = distutils.version.LooseVersion
    try:
        pkgconfig = ipc.Popen(
            ['pkg-config', '--modversion', package],
            stdout=ipc.PIPE, stderr=ipc.PIPE
        )
    except OSError:
        _, ex, _ = sys.exc_info()
        distutils.log.warn('cannot execute pkg-config: ' + str(ex))
        return V('0')
    stdout, stderr = pkgconfig.communicate()
    stdout = stdout.decode('ASCII', 'replace')
    stderr = stderr.decode('ASCII', 'replace')
    if pkgconfig.returncode:
        distutils.log.warn('pkg-config failed: ' + stderr.strip())
        return V('0')
    version = stdout.strip()
    return V(version)

djvulibre_version = pkgconfig_version('ddjvuapi')
py_version = get_version()

# Work-around for <https://bugs.python.org/issue969718>:
try:
    del os.environ['CFLAGS']
except KeyError:
    pass

class build_ext(distutils.command.build_ext.build_ext):

    config_filename = 'djvu/config.pxi'

    def run(self):
        new_config = [
            'DEF PY3K = {0}'.format(sys.version_info >= (3, 0)),
            'DEF PYTHON_DJVULIBRE_VERSION = "{0}"'.format(py_version),
            'DEF HAVE_MINIEXP_IO_T = {0}'.format(djvulibre_version >= '3.5.26'),
            'DEF HAVE_LANGINFO_H = {0}'.format(os.name == 'posix' and not mingw32cross),
        ]
        try:
            with open(self.config_filename, 'rt') as fp:
                old_config = fp.read()
        except IOError:
            old_config = ''
        if '\n'.join(new_config).strip() != old_config.strip():
            distutils.log.info('creating {conf!r}'.format(conf=self.config_filename))
            distutils.file_util.write_file(self.config_filename, new_config)
        distutils.command.build_ext.build_ext.run(self)

    def build_extensions(self):
        self.check_extensions_list(self.extensions)
        for ext in self.extensions:
            ext.sources = list(self.cython_sources(ext))
            self.build_extension(ext)

    def cython_sources(self, ext):
        for source in ext.sources:
            assert source.endswith('.pyx')
            target = '{mod}.c'.format(mod=source[:-4])
            yield target
            depends = [source, self.config_filename] + ext.depends
            if not (self.force or distutils.dep_util.newer_group(depends, target)):
                distutils.log.debug('not cythoning {ext.name!r} (up-to-date)'.format(ext=ext))
                continue
            distutils.log.info('cythoning {ext.name!r} extension'.format(ext=ext))
            def build_c(source, target):
                distutils.spawn.spawn(['cython', source])
                # XXX This is needed to work around <https://bugs.debian.org/607112>.
                # Fortunately, python-djvulibre doesn't really need __Pyx_GetVtable().
                file = open(target, 'r+')
                try:
                    contents = file.read()
                    contents = re.compile(
                        r'(?<=^static int __Pyx_GetVtable\(PyObject [*]dict, void [*]vtabptr\) {)$',
                        re.MULTILINE
                    ).sub(' return 0;', contents)
                    file.seek(0)
                    file.truncate()
                    file.write(contents)
                finally:
                    file.close()
            self.make_file(depends, target, build_c, [source, target])

class clean(distutils.command.clean.clean):

    def run(self):
        if self.all:
            for wildcard in 'djvu/*.c', 'djvu/config.pxi':
                filenames = glob.glob(wildcard)
                if filenames:
                    distutils.log.info('removing {0!r}'.format(wildcard))
                if self.dry_run:
                    continue
                for filename in filenames:
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
            for ext in ext_modules:
                __import__('djvu.' + ext)
            del sys.path[0]
            sphinx_setup_command.BuildDoc.run(self)
else:
    build_sphinx = None

compiler_flags = pkgconfig_build_flags('ddjvuapi')

setup_params = dict(
    name='python-djvulibre',
    version=py_version,
    author='Jakub Wilk',
    author_email='jwilk@jwilk.net',
    license='GNU GPL 2',
    description='Python support for the DjVu image format',
    long_description=__doc__.strip(),
    classifiers=classifiers,
    url='http://jwilk.net/software/python-djvulibre',
    platforms=['all'],
    packages=['djvu'],
    ext_modules=[
        distutils.command.build_ext.Extension(
            'djvu.{mod}'.format(mod=name),
            ['djvu/{mod}.pyx'.format(mod=name)],
            depends=(['djvu/common.pxi'] + glob.glob('djvu/*.pxd')),
            **compiler_flags
        )
        for name in ext_modules
    ],
    py_modules=['djvu.const'],
    cmdclass=dict(
        (cmd.__name__, cmd)
        for cmd in (build_ext, clean, build_sphinx)
        if cmd is not None
    )
)

if __name__ == '__main__':
    distutils_core.setup(**setup_params)

# vim:ts=4 sts=4 sw=4 et
