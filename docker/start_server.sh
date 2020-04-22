#!/bin/bash

# launch the server
echo "launch icubam server"
python3 scripts/run_server.py --port 8888 --config="/home/icubam/resources/${ICUBAM_CONFIG_FILE:-icubam.toml}"
