# encoding=UTF-8
# Copyright © 2010 Jakub Wilk <jwilk@jwilk.net>
#
# This package is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This package is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

import os
import sys

import distutils.ccompiler
import distutils.command.bdist_wininst
import distutils.cygwinccompiler
import distutils.sysconfig
import distutils.util

target = os.environ['python_djvulibre_mingw32']
directory = '%s/python%d.%d/' % ((target,) + sys.version_info[:2])
prefix = '%s-' % target

def get_platform():
   return 'win32'
distutils.util.get_platform = get_platform

def get_python_inc(*args, **kwargs):
    return directory
distutils.sysconfig.get_python_inc = get_python_inc

config_vars = distutils.sysconfig.get_config_vars()
config_vars['SO'] = '.pyd'

def get_default_compiler(*args, **kwargs):
    return 'mingw32'
distutils.ccompiler.get_default_compiler = get_default_compiler

class Mingw32CrossCompiler(distutils.cygwinccompiler.CygwinCCompiler):

    compiler_type = 'mingw32'

    def __init__(self, verbose=0, dry_run=0, force=0):
        distutils.cygwinccompiler.CygwinCCompiler.__init__ (self, verbose, dry_run, force)
        cc = 'gcc -O -Wall'
        cxx = 'g++ -O -Wall'
        ld = 'gcc -L%s' % directory
        self.set_executables(
            compiler = prefix + cc,
            compiler_so = prefix + cc,
            compiler_cxx = prefix + cxx,
            linker_exe  = prefix + ld,
            linker_so = prefix + ld + ' -shared'
        )
        self.dll_libraries = ['python%d%d' % sys.version_info[:2], 'msvcr']

distutils.cygwinccompiler.Mingw32CCompiler = Mingw32CrossCompiler

_bdist_wininst_run = distutils.command.bdist_wininst.bdist_wininst.run
def bdist_wininst_run(self):
    orig_platform = sys.platform
    sys.platform = 'win32'
    try:
        _bdist_wininst_run(self)
    finally:
        sys.platform = orig_platform
distutils.command.bdist_wininst.bdist_wininst.run = bdist_wininst_run

# vim:ts=4 sw=4 et
