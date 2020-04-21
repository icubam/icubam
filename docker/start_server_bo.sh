#!/bin/bash

# launch the server
echo "launch back-office server in ${ENV_MODE}"
python3 scripts/run_server.py --server=backoffice
