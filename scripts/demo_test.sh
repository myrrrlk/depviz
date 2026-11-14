#!/bin/sh
# Builds dependency graphs from test repositories (Linux / macOS).
cd "$(dirname "$0")/.." || exit 1

echo "=== Diamond: A needs B and C, both need D ==="
python3 -m src.main --config configs/test_basic.json
echo "Exit code: $?"

echo
echo "=== Diamond with filter 'D' ==="
python3 -m src.main --config configs/test_mode.json
echo "Exit code: $?"

echo
echo "=== Simple cycle: A, B, C ==="
python3 -m src.main --config configs/test_cycle.json
echo "Exit code: $?"

echo
echo "=== Several cycles and a self-dependency ==="
python3 -m src.main --config configs/test_complex.json
echo "Exit code: $?"

echo
echo "=== Same graph with filter 'E' ==="
python3 -m src.main --config configs/test_complex_filter.json
echo "Exit code: $?"