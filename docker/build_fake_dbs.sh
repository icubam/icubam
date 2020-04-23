#!/bin/bash

# launch the DB creation
echo "Build test db"
python3 scripts/populate_db_fake.py --config="/home/icubam/resources/${ICUBAM_CONFIG_FILE:-icubam.toml}"
