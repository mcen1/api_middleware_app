#!/bin/sh
curl http://127.0.0.1:8000/api/v1/automation/informational/health | grep allserviceshealthy
