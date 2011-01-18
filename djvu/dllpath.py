# encoding=UTF-8
# Copyright © 2011 Jakub Wilk <jwilk@jwilk.net>
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
Module aimed to ease finding DjVuLibre DLLs in non-standard locations.
'''

import os

if os.name != 'nt':
    raise ImportError('This module is for Windows only')

def guess_dll_path():
    import os
    import _winreg as winreg
    registry = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
    try:
        key = winreg.OpenKey(registry, r'Software\Microsoft\Windows\CurrentVersion\Uninstall\DjVuLibre+DjView')
        try:
            value, tp = winreg.QueryValueEx(key, 'UninstallString')
            if not isinstance(value, unicode):
                return
            path = os.path.dirname(value)
            if os.path.isfile(os.path.join(path, 'libdjvulibre.dll')):
                return path
        finally:
            winreg.CloseKey(key)
    except WindowsError:
        return
    finally:
        winreg.CloseKey(registry)

def set_dll_search_path(path=None):
    if path is None:
        path = guess_dll_path()
    if path is None:
        return
    if not isinstance(path, unicode):
        raise TypeError
    import ctypes
    ctypes.windll.kernel32.SetDllDirectoryW(path)
    return path

del os

# vim:ts=4 sw=4 et
