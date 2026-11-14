@echo off
rem Builds Mermaid diagrams and PNG images for three packages.
pushd "%~dp0.."

echo === spring-context 6.1.5 ===
python -m src.main --config configs\spring_context.json
echo Exit code: %ERRORLEVEL%

echo.
echo === jackson-databind 2.17.0 ===
python -m src.main --config configs\jackson_databind.json
echo Exit code: %ERRORLEVEL%

echo.
echo === guava 33.0.0-jre ===
python -m src.main --config configs\guava.json
echo Exit code: %ERRORLEVEL%

echo.
echo === Test repository with cycles ===
python -m src.main --config configs\test_complex.json
echo Exit code: %ERRORLEVEL%
popd