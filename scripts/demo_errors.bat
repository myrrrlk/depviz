@echo off
rem Shows error handling for the config file and all parameters.
pushd "%~dp0.."

echo === Config file does not exist ===
python -m src.main --config configs\missing.json
echo Exit code: %ERRORLEVEL%

echo.
echo === Config file is not valid JSON ===
python -m src.main --config configs\errors\invalid_json.json
echo Exit code: %ERRORLEVEL%

echo.
echo === Missing and unknown parameters ===
python -m src.main --config configs\errors\wrong_keys.json
echo Exit code: %ERRORLEVEL%

echo.
echo === Wrong repository_mode ===
python -m src.main --config configs\errors\wrong_mode.json
echo Exit code: %ERRORLEVEL%

echo.
echo === Wrong parameters in remote mode ===
python -m src.main --config configs\errors\wrong_remote.json
echo Exit code: %ERRORLEVEL%

echo.
echo === Wrong parameters in test mode ===
python -m src.main --config configs\errors\wrong_test.json
echo Exit code: %ERRORLEVEL%
popd