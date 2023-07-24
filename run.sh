#! /bin/bash

eval "$(conda shell.bash hook)"
conda activate autocommit
$(dirname "$0")/src/autocommit.py "$@"
conda deactivate
