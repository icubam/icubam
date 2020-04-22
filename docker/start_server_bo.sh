#!/bin/bash

# launch the server
echo "launch back-office server"
python3 scripts/run_server.py --server=backoffice  --config="/home/icubam/resources/${ICUBAM_CONFIG_FILE:-icubam.toml}"

