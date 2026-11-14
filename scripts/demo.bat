@echo off
rem Runs the program with correct configs (Windows).
pushd "%~dp0.."

echo === Default config (config.json, remote mode) ===
python -m src.main
echo Exit code: %ERRORLEVEL%

echo.
echo === Test mode (configs/test_mode.json) ===
python -m src.main --config configs\test_mode.json
echo Exit code: %ERRORLEVEL%
popd