#!/bin/sh
# Shows error handling for the config file and all parameters.
cd "$(dirname "$0")/.." || exit 1

echo "=== Config file does not exist ==="
python3 -m src.main --config configs/missing.json
echo "Exit code: $?"

echo
echo "=== Config file is not valid JSON ==="
python3 -m src.main --config configs/errors/invalid_json.json
echo "Exit code: $?"

echo
echo "=== Missing and unknown parameters ==="
python3 -m src.main --config configs/errors/wrong_keys.json
echo "Exit code: $?"

echo
echo "=== Wrong repository_mode ==="
python3 -m src.main --config configs/errors/wrong_mode.json
echo "Exit code: $?"

echo
echo "=== Wrong parameters in remote mode ==="
python3 -m src.main --config configs/errors/wrong_remote.json
echo "Exit code: $?"

echo
echo "=== Wrong parameters in test mode ==="
python3 -m src.main --config configs/errors/wrong_test.json
echo "Exit code: $?"