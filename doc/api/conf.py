# encoding=UTF-8

# Copyright © 2009-2015 Jakub Wilk <jwilk@jwilk.net>
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

import os
import codecs

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.pngmath',
    'sphinx.ext.inheritance_diagram',
]

templates_path = ['templates']
source_suffix = '.rst'
source_encoding = 'UTF-8'
master_doc = 'index'

import setup as _setup
project = _setup.setup_params['name']
version = release = _setup.py_version
_setup_file = codecs.open(
    os.path.splitext(_setup.__file__)[0] + '.py',
    'r', encoding='UTF-8'
)
try:
    for line in _setup_file:
        if line.startswith(u'# Copyright © '):
            copyright = line[14:].strip()
            break
finally:
    _setup_file.close()
del _setup, _setup_file

pygments_style = 'sphinx'

html_theme = 'haiku'
html_use_modindex = True
html_use_index = False

rst_epilog = '''
.. |djvu3ref| replace:: Lizardtech DjVu Reference
.. _djvu3ref: http://djvu.org/docs/DjVu3Spec.djvu

.. |djvused| replace:: djvused manual
.. _djvused: http://djvu.sourceforge.net/doc/man/djvused.html

.. |djvuext| replace:: Actual and proposed changes to the DjVu format
.. _djvuext: https://sourceforge.net/p/djvu/djvulibre-git/ci/release.3.5.23/tree/doc/djvuchanges.txt
'''

# vim:ts=4 sts=4 sw=4 et
