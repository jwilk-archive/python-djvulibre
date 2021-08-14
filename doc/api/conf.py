# encoding=UTF-8

# Copyright © 2009-2021 Jakub Wilk <jwilk@jwilk.net>
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

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.inheritance_diagram',
]

templates_path = ['templates']
source_suffix = '.rst'
source_encoding = 'UTF-8'
master_doc = 'index'

import setup as _setup
project = _setup.setup_params['name']
version = release = _setup.py_version

pygments_style = 'sphinx'

html_theme = 'haiku'
html_use_modindex = True
html_use_index = False
html_show_copyright = False
html_show_sphinx = False
html_static_path = ['static']

rst_epilog = '''
.. |djvu3ref| replace:: Lizardtech DjVu Reference
.. _djvu3ref: http://djvu.org/docs/DjVu3Spec.djvu

.. |djvused| replace:: djvused manual
.. _djvused: http://djvu.sourceforge.net/doc/man/djvused.html

.. |djvuext| replace:: Actual and proposed changes to the DjVu format
.. _djvuext: https://sourceforge.net/p/djvu/djvulibre-git/ci/release.3.5.23/tree/doc/djvuchanges.txt
'''

# With a bit of our help, docutils is capable of rendering our simple formulas.
# Sphinx math extension is not needed.
import sphinx.writers.html
del sphinx.writers.html.HTMLTranslator.visit_math
def setup(app):
    try:
        # added in Sphinx 1.8
        add_css_file = app.add_css_file
    except AttributeError:
        # deprecated in Sphinx 1.8, removed in 4.0
        add_css_file = app.add_stylesheet
    add_css_file('docutils-math.css')

# vim:ts=4 sts=4 sw=4 et
