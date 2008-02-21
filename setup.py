from distutils.core import setup
from distutils.extension import Extension
from Pyrex.Distutils import build_ext

EXT_MODULES = ('decode', 'sexpr')

setup(
	name = 'python-djvulibre',
	version = '0.1',
	author = 'Jakub Wilk',
	author_email = 'ubanus@users.sf.net',
	license = 'GNU GPL 2',
	platforms = ['all'],
	ext_package = 'djvu',
	ext_modules = \
	[
		Extension(name, ['djvu.%s.pyx' % name], libraries = ['djvulibre'])
		for name in EXT_MODULES
	],
	cmdclass = {'build_ext': build_ext}
)

# vim:ts=4 sw=4 noet
