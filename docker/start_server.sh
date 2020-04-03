#!/bin/bash

# conda init, activate environment
# and add current module (icubam) in edit/develop mode
conda init bash
conda activate icubam

# launch the server
echo "launch icubam server in mode $ENV_MODE"
python3 scripts/run_server.py --port 8888 --mode=$ENV_MODE --dotenv_path=/home/icubam/resources/icubam.env --config=/home/icubam/resources/icubam.toml
