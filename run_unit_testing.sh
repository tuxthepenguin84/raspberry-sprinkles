#!/bin/bash
trap "kill 0" EXIT
python3 rsapi.py & sleep 1 &&
python3 test_rsapi.py