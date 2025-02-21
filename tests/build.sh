#!/bin/bash

test_image=ska-tango-event-monitor-test

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )


mkdir -p ${SCRIPT_DIR}/dist

set -ex

cp ${SCRIPT_DIR}/../dist/pytango-9.5.0+dev-cp310-cp310-manylinux_2_35_x86_64.whl ${SCRIPT_DIR}/dist
docker build -t ${test_image} ${SCRIPT_DIR}

