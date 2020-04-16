#!/bin/bash

# launch the server
echo "launch sms server in mode ${ENV_MODE}"
python3 scripts/schedule_sms.py --mode="${ENV_MODE}" --config=/home/icubam/resources/config.toml
