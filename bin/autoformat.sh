#!/bin/bash -xe

PROJ_ROOT="$(dirname "${BASH_SOURCE[0]}")/.."
cd "${PROJ_ROOT}"

black ./src ./tests ./docs
ruff --fix ./src ./tests ./docs