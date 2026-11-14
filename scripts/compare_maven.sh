#!/bin/sh
# Compares the load order with real Maven (needs Maven installed).
cd "$(dirname "$0")/.." || exit 1

echo "=== depviz: load order of guava 33.0.0-jre ==="
python3 -m src.main --config configs/guava.json --load-order

echo
echo "=== Maven: dependency tree ==="
mvn -B -f compare/pom.xml dependency:tree

echo
echo "=== Maven: classpath order ===
mvn -B -f compare/pom.xml dependency:build-classpath