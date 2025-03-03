#!/bin/bash

# Builds the pytango wheel inside a docker image

pytango_version=$1
build_image=ska-tango-event-monitor-pytango-build

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

set -ex

docker_args="--build-arg PYTANGO_VERSION=${pytango_version}"
if [[ -n "${CI_COMMIT_SHORT_SHA}" ]]; then
    docker_args+="--build-arg CI_COMMIT_SHORT_SHA=${CI_COMMIT_SHORT_SHA}"
fi

docker build -t ${build_image} ${SCRIPT_DIR} ${docker_args}
id=$(docker create ${build_image})
docker cp "$id:/usr/src/pytango/wheelhouse" ${SCRIPT_DIR}
docker rm -v $id
