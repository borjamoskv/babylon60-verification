#!/bin/sh
set -eu

mirror_dir=$(CDPATH='' cd "$(dirname "$0")" && pwd)
cd "$mirror_dir"

python3 verify.py
exec lake build
