#!/bin/sh
source /usr/CHANGEME/envvars.sh
uvicorn main:app --host 0.0.0.0 --port 8000 --root-path /CHANGEMEpi
