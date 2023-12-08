#!/bin/bash -xe

PROJ_ROOT="$(dirname "${BASH_SOURCE[0]}")/.."
cd "${PROJ_ROOT}"

ls ./

black ./src ./tests
ruff --fix ./src ./tests