#!/bin/bash

# A simple script which will poll the provided URLs and, if all of them are
# unreachable simultaneously, exit with a non-zero status.

TMPDIR="$(mktemp --directory)"
trap 'rm -rf -- "$TMPDIR"' EXIT

while sleep 1; do
  echo "Polling..."
  rm -rf "$TMPDIR/success" 
  for url in "$@"; do
    (
      if timeout 1 curl "$url" --fail --silent -o /dev/null; then
        echo "UP   $url"
        touch "$TMPDIR/success"
      else
        echo "DOWN $url"
      fi
    )&
  done
  wait

  if [ ! -f "$TMPDIR/success" ]; then
    echo "All URLs down!"
    exit 1
  fi
done
