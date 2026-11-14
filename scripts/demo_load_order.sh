#!/bin/sh
# Shows the load order for test repositories (Linux / macOS).
cd "$(dirname "$0")/.." || exit 1

echo "=== Chain with a shared package (diamond) ==="
python3 -m src.main --config configs/test_basic.json --load-order
echo "Exit code: $?"

echo
echo "=== Several levels without cycles ==="
python3 -m src.main --config configs/test_layers.json --load-order
echo "Exit code: $?"

echo
echo "=== Diamond with filter 'D' ==="
python3 -m src.main --config configs/test_mode.json --load-order
echo "Exit code: $?"

echo
echo "=== Simple cycle ==="
python3 -m src.main --config configs/test_cycle.json --load-order
echo "Exit code: $?"

echo
echo "=== Several cycles and a self-dependency ==="
python3 -m src.main --config configs/test_complex.json --load-order
echo "Exit code: $?"