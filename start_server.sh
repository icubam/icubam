#!/bin/bash

# conda init, activate environment
# and add current module (icubam) in edit/develop mode
conda init bash
conda activate icubam
pip install -e .

# generate fake DB and overide default/empty one
# python scripts/populate_db_fake.py
# mv icubam.db resources/

# launch the server
python3 scripts/run_server.py --port 8888 --dotenv_path=/home/icubam/resources/icubam.env --config=/home/icubam/resources/icubam.toml
