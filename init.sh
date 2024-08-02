#!/usr/bin/bash

TOOL=$1

TOOLREQ="${TOOL}.requirements.txt"
TOOLENV=".venv_${TOOL}"

if [ ! -f $TOOLREQ ]; then
    echo "Tool requirements file '${TOOLREQ}' not found"
    exit 1
fi

python3 -m venv $TOOLENV
source $TOOLENV/bin/activate
pip install -r $TOOLREQ
