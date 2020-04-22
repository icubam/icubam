#!/bin/bash

# launch the server
echo "launch sms server"
python3 scripts/schedule_sms.py --config="/home/icubam/resources/${ICUBAM_CONFIG_FILE:-icubam.toml}"
