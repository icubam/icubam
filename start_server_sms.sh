#!/bin/bash

# conda init, activate environment
# and add current module (icubam) in edit/develop mode
conda init bash
conda activate icubam
pip install -e .

echo "launch sms server"
