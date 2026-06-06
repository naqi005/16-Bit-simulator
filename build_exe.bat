@echo off
echo ============================================================
echo   16-bit Processor Simulator - Build EXE
echo   CE-222 COAL Project - FCSE GIKI
echo ============================================================
echo.

cd /d "%~dp0"

echo Step 1: Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.8+ and add to PATH.
    pause
    exit /b 1
)

echo Step 2: Installing PyInstaller...
pip install pyinstaller --quiet

echo Step 3: Building EXE...
pyinstaller --onefile --windowed ^
    --name "16bit_Processor_Simulator" ^
    --add-data "examples\fibonacci.asm;examples" ^
    --add-data "examples\arithmetic_demo.asm;examples" ^
    --add-data "examples\addressing_modes.asm;examples" ^
    --add-data "examples\subroutine.asm;examples" ^
    --clean ^
    gui.py

if errorlevel 1 (
    echo.
    echo BUILD FAILED. See errors above.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   BUILD SUCCESSFUL!
echo   EXE: dist\16bit_Processor_Simulator.exe
echo ============================================================
echo.
echo Double-click the EXE to run the simulator.
pause