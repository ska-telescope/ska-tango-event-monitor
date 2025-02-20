include .make/base.mk

include .make/python.mk

build-pytango950:
	@mkdir -p dist/
	build_pytango/9.5.0/build.sh
	cp build_pytango/9.5.0/wheelhouse/* dist/
