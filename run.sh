#! /bin/bash
eval "$(conda shell.bash hook)"
conda activate codecommit
./app/codecommit.py
conda deactivate
