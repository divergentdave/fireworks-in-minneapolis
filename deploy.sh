#!/bin/sh
if [ -d deploy ]
then
    rsync --verbose --progress --stats --compress --recursive --times --perms --delete deploy/* pi:/var/www/fireworks
fi
