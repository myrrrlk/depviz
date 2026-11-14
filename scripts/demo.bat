@echo off
rem Shows direct dependencies of several packages (Windows).
pushd "%~dp0.."

echo === spring-core 6.1.5 (config.json) ===
python -m src.main
echo Exit code: %ERRORLEVEL%

echo.
echo === commons-text 1.12.0 ===
python -m src.main --config configs\commons_text.json
echo Exit code: %ERRORLEVEL%

echo.
echo === guava 33.0.0-jre ===
python -m src.main --config configs\guava.json
echo Exit code: %ERRORLEVEL%

echo.
echo === Test repository, package A ===
python -m src.main --config configs\test_mode.json
echo Exit code: %ERRORLEVEL%
popd