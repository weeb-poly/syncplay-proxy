#!/usr/bin/env bash

PYZ_FILE="syncplay.pyz"

[ ! -e "${PYZ_FILE}" ] || rm "${PYZ_FILE}"

pip install -r <(pipenv lock -r) --target dist/

cp -r -t dist syncplay

shiv \
  --site-packages dist \
  --uncompressed \
  --reproducible \
  -p '/usr/bin/env python3' \
  -o "${PYZ_FILE}" \
  -e syncplay.__main__:main

rm -r dist
