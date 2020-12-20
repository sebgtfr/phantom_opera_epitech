#!/bin/bash

cp -f ./inspector.py ./phantom_opera/my_inspector.py

cd ./phantom_opera

python3 ./server.py &

sleep 1

python3 ./my_inspector.py &

python3 ./random_fantom.py &