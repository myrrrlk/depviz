@echo off
rem Builds dependency graphs from test repositories (Windows).
pushd "%~dp0.."

echo === Diamond: A needs B and C, both need D ===
python -m src.main --config configs\test_basic.json
echo Exit code: %ERRORLEVEL%

echo.
echo === Diamond with filter 'D' ===
python -m src.main --config configs\test_mode.json
echo Exit code: %ERRORLEVEL%

echo.
echo === Simple cycle: A, B, C ===
python -m src.main --config configs\test_cycle.json
echo Exit code: %ERRORLEVEL%

echo.
echo === Several cycles and a self-dependency ===
python -m src.main --config configs\test_complex.json
echo Exit code: %ERRORLEVEL%

echo.
echo === Same graph with filter 'E' ===
python -m src.main --config configs\test_complex_filter.json
echo Exit code: %ERRORLEVEL%
popd