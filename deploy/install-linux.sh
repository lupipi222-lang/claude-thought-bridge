#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 -m venv "$project_dir/.venv"
"$project_dir/.venv/bin/pip" install -e "$project_dir"
if [[ ! -f "$project_dir/.env" ]]; then
  cp "$project_dir/.env.example" "$project_dir/.env"
  chmod 600 "$project_dir/.env"
  echo "Created $project_dir/.env; fill it before starting services."
fi
echo "Installed. Run: $project_dir/.venv/bin/thought-bridge doctor"
