#!/bin/bash

# conda init, activate environment
# and add current module (icubam) in edit/develop mode
conda init bash
conda activate icubam

# launch the server
echo "launch back-office server in mode ${ENV_MODE}"
python3 scripts/run_server.py --mode="${ENV_MODE}" --server=backoffice