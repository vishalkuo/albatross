#!/bin/bash

if [ $# -eq 0 ]
  then
    echo "No arguments supplied, exiting..."
    exit 1
fi

TO_EXPORT=$1
echo "exporting $TO_EXPORT"


cd env/lib/python3.7/site-packages/
zip -r9 export.zip .
mv export.zip ../../../../
cd ../../../../
zip -g export.zip $TO_EXPORT

