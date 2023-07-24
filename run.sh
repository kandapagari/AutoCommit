#! /bin/bash

eval "$(conda shell.bash hook)"

find_in_conda_env(){
    conda env list | grep "${@}" >/dev/null 2>/dev/null
}

if find_in_conda_env ".*autocommit.*" ; then
    conda activate autocommit
else
    echo "autocommit env not found creating it"
    conda create -n autocommit python=3.10 -y
    conda activate autocommit
    pip install poetry
    poetry install
fi
$(dirname "$0")/src/autocommit.py "$@"
conda deactivate
