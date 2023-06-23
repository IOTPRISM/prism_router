#!/bin/bash

#run tests

CURRENT_DIR="$(dirname "$(readlink -f "$0")")"
python3 -m unittest discover -s $CURRENT_DIR -p '*_tests.py'