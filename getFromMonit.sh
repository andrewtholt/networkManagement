#!/bin/bash


echo $#

if [ $# -eq 0 ]; then
    echo "getFromMinit.sh <ip address>"
fi

echo $1

# wget -O monit.xml  --user="admin" --password="monit" http://192.168.10.124:2812/_status?format=xml
# wget -O monit.xml  --user="admin" --password="monit" http://${1}:2812/_status?format=xml
wget -O - --user="admin" --password="monit" http://${1}:2812/_status?format=xml | xml-to-json | jq .
