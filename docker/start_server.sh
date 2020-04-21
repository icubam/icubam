#!/bin/bash

# launch the server
echo "launch icubam server in mode ${ENV_MODE}"
python3 scripts/run_server.py --port 8888 --config="/home/icubam/resources/config_${ENV_MODE}.toml"
