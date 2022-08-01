# encoding=UTF-8

# Copyright © 2007-2022 Jakub Wilk <jwilk@jwilk.net>
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

'''
*python-djvulibre* is a set of Python bindings for
the `DjVuLibre <http://djvu.sourceforge.net/>`_ library,
an open source implementation of `DjVu <http://djvu.org/>`_.
'''

import glob
import io
import os
import re
import subprocess as ipc
import sys

need_setuptools = False
if os.name == 'nt':
    import djvu.dllpath
    need_setuptools = True

if need_setuptools:
    import setuptools.extension
    del setuptools.extension
    del setuptools

import distutils.core
import distutils.ccompiler
import distutils.command.build_ext
import distutils.command.sdist
import distutils.dep_util
import distutils.dir_util
import distutils.version

try:
    import sphinx.setup_command as sphinx_setup_command
except ImportError:
    sphinx_setup_command = None

try:
    from wheel.bdist_wheel import bdist_wheel
except ImportError:
    bdist_wheel = None

try:
    import distutils644
except ImportError:
    pass
else:
    distutils644.install()

type(b'')  # Python >= 2.6 is required
type(u'')  # Python 2.X or >= 3.3 is required

def ext_modules():
    for pyx_file in glob.iglob(os.path.join('djvu', '*.pyx')):
        module, _ = os.path.splitext(os.path.basename(pyx_file))
        yield module
ext_modules = list(ext_modules())

def get_version():
    path = os.path.join(os.path.dirname(__file__), 'doc', 'changelog')
    with io.open(path, encoding='UTF-8') as file:
        line = file.readline()
    return line.split()[1].strip('()')

def run_pkgconfig(*cmdline):
    cmdline = ['pkg-config'] + list(cmdline)
    try:
        pkgconfig = ipc.Popen(
            cmdline,
            stdout=ipc.PIPE, stderr=ipc.PIPE
        )
    except EnvironmentError as exc:
        msg = 'cannot execute pkg-config: {exc.strerror}'.format(exc=exc)
        distutils.log.warn(msg)
        return
    stdout, stderr = pkgconfig.communicate()
    stdout = stdout.decode('ASCII')
    stderr = stderr.decode('ASCII', 'replace')
    if pkgconfig.returncode != 0:
        distutils.log.warn('pkg-config failed:')
        for line in stderr.splitlines():
            distutils.log.warn('  ' + line)
        return
    return stdout

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
                include_dirs=[os.path.join(dll_path, 'include')],
                library_dirs=[os.path.join(dll_path)],
                libraries=['libdjvulibre'],
            )
    stdout = run_pkgconfig('--libs', '--cflags', *packages)
    if stdout is None:
        return fallback
    kwargs.setdefault('extra_link_args', [])
    kwargs.setdefault('extra_compile_args', [])
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
    stdout = run_pkgconfig('--modversion', package)
    if stdout is None:
        return
    return stdout.strip()

def get_djvulibre_version():
    version = pkgconfig_version('ddjvuapi')
    if version is None:
        if os.name == 'posix':
            raise distutils.errors.DistutilsError('cannot determine DjVuLibre version')
        elif os.name == 'nt':
            version = djvu.dllpath._guess_dll_version()
    version = version or '0'
    return distutils.version.LooseVersion(version)

def get_cython_version():
    cmdline = [sys.executable, '-m', 'cython', '--version']
    cmd = ipc.Popen(cmdline, stdout=ipc.PIPE, stderr=ipc.STDOUT)
    stdout, stderr = cmd.communicate()
    if not isinstance(stdout, str):
        stdout = stdout.decode('ASCII')
    match = re.match(r'\ACython version (\d\S+)', stdout)
    if match:
        ver = match.group(1)
    else:
        ver = '0'
    return distutils.version.LooseVersion(ver)

py_version = get_version()
cython_version = get_cython_version()
if str is bytes:
    # Python 2.X
    req_cython_version = '0.19.1'
else:
    # Python 3.X
    req_cython_version = '0.20'

# Work-around for <https://bugs.python.org/issue969718>:
os.environ.pop('CFLAGS', None)

class build_ext(distutils.command.build_ext.build_ext):

    def run(self):
        djvulibre_version = get_djvulibre_version()
        if djvulibre_version != '0' and djvulibre_version < '3.5.21':
            raise distutils.errors.DistutilsError('DjVuLibre >= 3.5.21 is required')
        compiler_flags = pkgconfig_build_flags('ddjvuapi')
        for extension in self.extensions:
            for attr, flags in compiler_flags.items():
                getattr(extension, attr)
                setattr(extension, attr, flags)
        new_config = [
            'DEF PY3K = {0}'.format(sys.version_info >= (3, 0)),
            'DEF PYTHON_DJVULIBRE_VERSION = b"{0}"'.format(py_version),
            'DEF HAVE_MINIEXP_IO_T = {0}'.format(djvulibre_version >= '3.5.26'),
            'DEF HAVE_LANGINFO_H = {0}'.format(os.name == 'posix'),
            'DEF WINDOWS = {0}'.format(os.name == 'nt'),
        ]
        self.src_dir = src_dir = os.path.join(self.build_temp, 'src')
        distutils.dir_util.mkpath(src_dir)
        self.config_path = os.path.join(src_dir, 'config.pxi')
        try:
            with open(self.config_path, 'rt') as fp:
                old_config = fp.read()
        except IOError:
            old_config = ''
        if str.join('\n', new_config).strip() != old_config.strip():
            distutils.log.info('creating {conf!r}'.format(conf=self.config_path))
            distutils.file_util.write_file(self.config_path, new_config)
        distutils.command.build_ext.build_ext.run(self)

    def build_extensions(self):
        self.check_extensions_list(self.extensions)
        for ext in self.extensions:
            ext.sources = list(self.cython_sources(ext))
            self.build_extension(ext)

    def cython_sources(self, ext):
        for source in ext.sources:
            source_base = os.path.basename(source)
            # This assertion may fail with setuptools < 0.6.16, which didn't understand Cython.
            assert source_base.endswith('.pyx'), '{path} is not a .pyx file'.format(path=source_base)
            target = os.path.join(
                self.src_dir,
                '{mod}.c'.format(mod=source_base[:-4])
            )
            yield target
            depends = [source, self.config_path] + ext.depends
            if not (self.force or distutils.dep_util.newer_group(depends, target)):
                distutils.log.debug('not cythoning {ext.name!r} (up-to-date)'.format(ext=ext))
                continue
            distutils.log.info('cythoning {ext.name!r} extension'.format(ext=ext))
            def build_c(source, target):
                if cython_version < req_cython_version:
                    raise distutils.errors.DistutilsError('Cython >= {ver} is required'.format(ver=req_cython_version))
                distutils.spawn.spawn([
                    sys.executable, '-m', 'cython',
                    '-I', os.path.dirname(self.config_path),
                    '-o', target,
                    source,
                ])
            self.make_file(depends, target, build_c, [source, target])

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

class sdist(distutils.command.sdist.sdist):

    def maybe_move_file(self, base_dir, src, dst):
        src = os.path.join(base_dir, src)
        dst = os.path.join(base_dir, dst)
        if os.path.exists(src):
            self.move_file(src, dst)

    def make_release_tree(self, base_dir, files):
        distutils.command.sdist.sdist.make_release_tree(self, base_dir, files)
        self.maybe_move_file(base_dir, 'COPYING', 'doc/COPYING')

classifiers = '''
Development Status :: 4 - Beta
Intended Audience :: Developers
License :: OSI Approved :: GNU General Public License (GPL)
Operating System :: POSIX
Programming Language :: Cython
Programming Language :: Python
Programming Language :: Python :: 2
Programming Language :: Python :: 3
Topic :: Multimedia :: Graphics
Topic :: Multimedia :: Graphics :: Graphics Conversion
Topic :: Text Processing
'''.strip().splitlines()

meta = dict(
    name='python-djvulibre',
    version=py_version,
    author='Jakub Wilk',
    author_email='jwilk@jwilk.net',
    license='GNU GPL 2',
    description='Python support for the DjVu image format',
    long_description=__doc__.strip(),
    classifiers=classifiers,
    url='https://jwilk.net/software/python-djvulibre',
)

setup_params = dict(
    packages=['djvu'],
    ext_modules=[
        distutils.command.build_ext.Extension(
            'djvu.{mod}'.format(mod=name),
            ['djvu/{mod}.pyx'.format(mod=name)],
            depends=(['djvu/common.pxi'] + glob.glob('djvu/*.pxd')),
        )
        for name in ext_modules
    ],
    py_modules=['djvu.const'],
    cmdclass=dict(
        (cmd.__name__, cmd)
        for cmd in (build_ext, build_sphinx, sdist, bdist_wheel)
        if cmd is not None
    ),
    **meta
)

if __name__ == '__main__':
    egg_info_for_pip = ('setuptools' in sys.modules) and (sys.argv[1] == 'egg_info')
    if (cython_version < req_cython_version) and egg_info_for_pip:
        # This shouldn't happen with pip >= 10, thanks to PEP-518 support.
        # For older versions, we use this hack to trick it into installing Cython:
        distutils.core.setup(
            install_requires=['Cython>={ver}'.format(ver=req_cython_version)],
            # Conceptually, “setup_requires” would make more sense than
            # “install_requires”, but the former is not supported by pip.
            **meta
        )
    else:
        distutils.core.setup(**setup_params)

# vim:ts=4 sts=4 sw=4 et
