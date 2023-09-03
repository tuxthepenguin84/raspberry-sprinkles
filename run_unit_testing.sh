#!/bin/bash
trap "kill 0" EXIT
python rsapi.py & sleep 1 &&
python test_rsapi.py