#!/bin/bash

echo "Starting NapNapGunicorn DEV"

cd /usr/share/nginx/NapNap-DEV
source env/bin/activate
exec gunicorn Init:app\
	--name NapNapDEV\
	-w 3\
	--bind 0.0.0.0:8081\
	--user=nginx\
	--log-file=/usr/share/nginx/logs/NapNapDev.log\
	-D
cd $OLDPWD
