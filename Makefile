include .make/base.mk

include .make/python.mk

build-pytango950:
	@mkdir -p dist/
	build_pytango/9.5/build.sh 9.5.0
	cp build_pytango/9.5/wheelhouse/* dist/

build-pytango951:
	@mkdir -p dist/
	build_pytango/9.5/build.sh 9.5.1
	cp build_pytango/9.5/wheelhouse/* dist/
