from distutils.core import setup
from distutils.extension import Extension
from Pyrex.Distutils import build_ext

setup(
	name = 'djvulibre',
	ext_modules = \
	[
		Extension('miniexp', ['miniexp.pyx'])
	],
	cmdclass = {'build_ext': build_ext}
)

# vim:ts=4 sw=4 noet
