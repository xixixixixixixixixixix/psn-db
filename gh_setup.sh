#!/usr/bin/env bash
# GitHub side of the pipeline: repo, secrets, permissions pushed via gh_setup.py.
set -euo pipefail
cd "$(dirname "$0")"
. deploy/.gh.env
pip install --quiet pynacl 2>/dev/null || pip3 install --quiet pynacl
python3 deploy/gh_setup.py
