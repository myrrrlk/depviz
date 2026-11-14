#!/bin/sh
# Shows direct dependencies of several packages (Linux / macOS).
cd "$(dirname "$0")/.." || exit 1

echo "=== spring-core 6.1.5 (config.json) ==="
python3 -m src.main
echo "Exit code: $?"

echo
echo "=== commons-text 1.12.0 ==="
python3 -m src.main --config configs/commons_text.json
echo "Exit code: $?"

echo
echo "=== guava 33.0.0-jre ==="
python3 -m src.main --config configs/guava.json
echo "Exit code: $?"

echo
echo "=== Test repository, package A ==="
python3 -m src.main --config configs/test_mode.json
echo "Exit code: $?"