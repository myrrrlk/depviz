@echo off
rem Shows the dependency tree built by Maven (needs Maven installed).
pushd "%~dp0.."

echo === Maven: dependency tree of the three packages ===
call mvn -B -f compare\visual\pom.xml dependency:tree
popd