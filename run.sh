#!/usr/bin/bash

TOOL=$1
shift

TOOLREQ="${TOOL}.requirements.txt"
TOOLENV=".venv_${TOOL}"

if [ ! -d "$TOOLENV" ]; then
    echo "Tool environment '${TOOLENV}' is not found!"
    if [ -f $TOOLREQ ]; then
        echo "to create environment, run ./init.sh ${TOOL}"
    else
        echo "check the name of the tool"
    fi
    exit 1
fi

source $TOOLENV/bin/activate
python3 $TOOL.py $@
