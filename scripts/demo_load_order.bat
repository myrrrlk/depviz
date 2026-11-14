@echo off
rem Shows the load order for test repositories (Windows).
pushd "%~dp0.."

echo === Chain with a shared package (diamond) ===
python -m src.main --config configs\test_basic.json --load-order
echo Exit code: %ERRORLEVEL%

echo.
echo === Several levels without cycles ===
python -m src.main --config configs\test_layers.json --load-order
echo Exit code: %ERRORLEVEL%

echo.
echo === Diamond with filter 'D' ===
python -m src.main --config configs\test_mode.json --load-order
echo Exit code: %ERRORLEVEL%

echo.
echo === Simple cycle ===
python -m src.main --config configs\test_cycle.json --load-order
echo Exit code: %ERRORLEVEL%

echo.
echo === Several cycles and a self-dependency ===
python -m src.main --config configs\test_complex.json --load-order
echo Exit code: %ERRORLEVEL%
popd