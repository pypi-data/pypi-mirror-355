#!/usr/bin/env sh
uv run sortition gsheet \
  -n 52 \
  --auth-json-file ~/secret_do_not_commit.json \
  -S ~/sf_stratification_settings.toml \
  -g "Dev Copy of RSPCA 2025 Our Working Version" \
  -f "Categories" \
  -p "Respondents" \
  -s "Original Selected" \
  -r "Remaining - 1"
