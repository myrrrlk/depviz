#!/bin/sh
# Runs the program with correct configs (Linux / macOS).
cd "$(dirname "$0")/.." || exit 1

echo "=== Default config (config.json, remote mode) ==="
python3 -m src.main
echo "Exit code: $?"

echo
echo "=== Test mode (configs/test_mode.json) ==="
python3 -m src.main --config configs/test_mode.json
echo "Exit code: $?"