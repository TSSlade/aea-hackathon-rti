#!/usr/bin/env bash

count=${1:-300}  # default to 100 if not provided

for ((i=0; i<count; i++)); do
  uuidgen
done