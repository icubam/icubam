#!/bin/bash

if [ $# -ne 1 ]
then
	  echo "usage: $0 HOSTNAME"
	  echo "   where HOSTNAME is the Internet hostname to validate with Let's Encrypt/Certbot"
      echo ""
      echo "   example: $0 www.example.org"
	  exit
fi

echo "Replace all occurences of WEB_HOSTNAME in nginx config file with $1"

for f in ../configs/nginx/* ; do
  if [ -f $f ]; then
    echo "Process $f"
    # empty extension required on MacOSX
    sed -i '' 's|WEB_HOSTNAME|'"$1"'|g' $f;
  fi
done

echo "Process set_hostname_nginx.sh"
sed -i '' 's|WEB_HOSTNAME|'"$1"'|g' set_hostname_nginx.sh
