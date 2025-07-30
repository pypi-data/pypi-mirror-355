#!/usr/bin/env sh
uv run sortition csv \
  -n 22 \
  -S ignore/sf_stratification_settings.toml \
  -f tests/fixtures/features.csv \
  -p tests/fixtures/candidates.csv \
  -s selected.csv \
  -r remaining.csv
