from distutils.core import setup
from distutils.extension import Extension
from Pyrex.Distutils import build_ext

EXT_MODULES = ('ddjvu', 'miniexp')

setup(
	name = 'djvulibre',
	ext_modules = \
	[
		Extension(name, ['%s.pyx' % name], libraries = ['djvulibre'])
		for name in EXT_MODULES
	],
	cmdclass = {'build_ext': build_ext}
)

# vim:ts=4 sw=4 noet
