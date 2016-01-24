#!/bin/bash

cd /home/cloudcalc/server
source ./bin/activate

pip install python-mysqldb
pip install mysql-python
echo "Success!!!"

