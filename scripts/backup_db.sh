#!/bin/bash

if [ $# -ne 2 ]; then
  echo "backup_db.sh requires a valid sqlite3 db to be backuped as argument."
  echo "  i.e.: ./backup_db.sh /home/icubam/test.db /home/icubam/test.db.bak"
  echo "This script guarantees backup even if a write access is performed at the same time by the application."
  exit 1
fi

if [ ! -f "$1" ]; then
  echo "$1 does not exist"
  exit 1
fi

sqlite3 "$1" ".backup $2"
exit 0