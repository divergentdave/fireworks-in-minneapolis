#!/bin/sh
rm -rf deploy
mkdir deploy
bower install
cp -p bower_components/normalize.css/normalize.css css
cp -p bower_components/milligram/dist/milligram.min.css css
.virtualenv/bin/python extract.py
cp -pR css data fireworks.ics fonts index.html deploy
