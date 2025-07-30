#!/usr/bin/env sh
uv run sortition gen-sample \
  -n 90 \
  -S ignore/sf_stratification_settings.toml \
  -f tests/fixtures/features.csv \
  -p sample.csv
