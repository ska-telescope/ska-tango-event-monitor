#!/bin/bash

if [[ -z "${CI_COMMIT_SHORT_SHA}" ]]; then
    sed -E -i.bak 's|^(version.*=.*")(.*)(")$|\1\2+dev\3|g' pyproject.toml && rm pyproject.toml.bak
else
    sed -E -i.bak 's|^(version.*=.*")(.*)(")$|\1\2+dev.'"c${CI_COMMIT_SHORT_SHA}"'\3|g' pyproject.toml && rm pyproject.toml.bak
fi
