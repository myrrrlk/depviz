#!/bin/sh
# Builds Mermaid diagrams and PNG images for three packages.
cd "$(dirname "$0")/.." || exit 1

echo "=== spring-context 6.1.5 ==="
python3 -m src.main --config configs/spring_context.json
echo "Exit code: $?"

echo
echo "=== jackson-databind 2.17.0 ==="
python3 -m src.main --config configs/jackson_databind.json
echo "Exit code: $?"

echo
echo "=== guava 33.0.0-jre ==="
python3 -m src.main --config configs/guava.json
echo "Exit code: $?"

echo
echo "=== Test repository with cycles ==="
python3 -m src.main --config configs/test_complex.json
echo "Exit code: $?"