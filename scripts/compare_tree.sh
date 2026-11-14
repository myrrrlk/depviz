#!/bin/sh
# Shows the dependency tree built by Maven (needs Maven installed).
cd "$(dirname "$0")/.." || exit 1

echo "=== Maven: dependency tree of the three packages ==="
mvn -B -f compare/visual/pom.xml dependency:tree