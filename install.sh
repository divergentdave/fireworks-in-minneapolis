#!/bin/sh
set -e
TOPLEVEL=$(git rev-parse --show-toplevel)
if [ ! -d "$TOPLEVEL/.virtualenv" ]
then
    python3 -m virtualenv --version >/dev/null || { sudo pip install virtualenv; }
    python3 -m virtualenv -p python3 "$TOPLEVEL/.virtualenv"
fi
"$TOPLEVEL/.virtualenv/bin/pip" install -r "$TOPLEVEL/requirements.txt"
if [ ! -f "$TOPLEVEL/.git/hooks/pre-commit" ]
then
    ln -s "$TOPLEVEL/pre-commit.sh" "$TOPLEVEL/.git/hooks/pre-commit"
fi
