#! /bin/bash

eval "$(conda shell.bash hook)"
conda activate codecommit
$(dirname "$0")/src/autocommit.py "$@"
conda deactivate
