#!/bin/sh
rm -rf deploy
mkdir deploy
bower install
cp bower_components/normalize.css/normalize.css css
cp bower_components/milligram/dist/milligram.min.css css
.virtualenv/bin/python extract.py
cp -R css data fireworks.ics fonts index.html deploy
