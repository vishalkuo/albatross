#!/bin/bash

echo "exporting..."


cd env/lib/python3.7/site-packages/
zip -r9 -q export.zip .
mv export.zip ../../../../
cd ../../../../
zip -g export.zip *.py
