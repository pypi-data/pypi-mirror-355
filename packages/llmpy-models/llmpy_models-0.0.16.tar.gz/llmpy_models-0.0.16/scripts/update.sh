#!/usr/bin/env bash

# run this script through the justfile

set -euo pipefail

OUT_FILE='src/llmpy_models/llmpy_models.py'
TEMP_FILE='llmpy_models.py'

# source virtual env
source .venv/bin/activate

# run generator (creates llmpy_models.py in root)
python scripts/generator.py

# check if different from current version
if diff -q "$OUT_FILE" "$TEMP_FILE" >/dev/null; then
    rm "$TEMP_FILE"
    echo "No changes detected, skipping update"
    exit 0
fi

# move to proper location
mv "$TEMP_FILE" "$OUT_FILE"

# remove old dist
rm -rf dist/

# bump version
current=$(grep 'version = ' pyproject.toml | cut -d'"' -f2)
IFS='.' read -ra parts <<< "$current"
new="${parts[0]}.${parts[1]}.$((parts[2] + 1))"
sed -i '' "s/version = \"$current\"/version = \"$new\"/" pyproject.toml
echo "Bumped version from $current to $new"

# build and upload
python -m build
python -m twine upload --config-file .pypirc dist/*