#! /bin/bash
eval "$(conda shell.bash hook)"
conda activate codecommit
if [ $# -eq 0 ];
then
    ./app/codecommit.py
    conda deactivate
    exit 0
fi
conda deactivate
exit 0