@echo off
rem Compares the load order with real Maven (needs Maven installed).
pushd "%~dp0.."

echo === depviz: load order of guava 33.0.0-jre ===
python -m src.main --config configs\guava.json --load-order

echo.
echo === Maven: dependency tree ===
call mvn -B -f compare\pom.xml dependency:tree

echo.
echo === Maven: classpath order ===
call mvn -B -f compare\pom.xml dependency:build-classpath
popd