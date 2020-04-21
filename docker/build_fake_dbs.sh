#!/bin/bash

# conda init, activate environment
# and add current module (icubam) in edit/develop mode
conda init bash
conda activate icubam

# launch the server
pwd
ls -a
echo "Build test db"
PYTHONPATH=. python scripts/populate_db_fake.py --config=resources/config_dev.toml

echo "Build icubam db"
PYTHONPATH=. python scripts/populate_db_fake.py --config=resources/config_prod.toml

cp ./test.db ./db/
cp ./icubam.db ./db/
