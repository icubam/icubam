#!/bin/bash

# launch the server
echo "launch icubam server in mode ${ENV_MODE}"
python3 scripts/run_server.py --port 8888 --mode="${ENV_MODE}" --config=/home/icubam/resources/config.toml
