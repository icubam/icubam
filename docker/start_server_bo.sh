#!/bin/bash

# launch the server
echo "launch back-office server in mode ${ENV_MODE}"
python3 scripts/run_server.py --mode="${ENV_MODE}" --server=backoffice