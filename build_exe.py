"""
Build script for 16-bit Processor Simulator EXE.
Requires PyInstaller:  pip install pyinstaller

Run:  python build_exe.py
The exe will be in:  dist/16bit_Processor_Simulator.exe
"""

import subprocess
import sys
import os

def main():
    # Install PyInstaller if missing
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])

    base = os.path.dirname(os.path.abspath(__file__))

    # Collect example files as data
    examples_dir = os.path.join(base, 'examples')
    example_files = []
    if os.path.isdir(examples_dir):
        for f in os.listdir(examples_dir):
            if f.endswith('.asm'):
                example_files.append(
                    f'--add-data={os.path.join(examples_dir, f)};examples'
                )

    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',
        '--windowed',
        '--name=16bit_Processor_Simulator',
        '--clean',
        f'--distpath={os.path.join(base, "dist")}',
        f'--workpath={os.path.join(base, "build")}',
        f'--specpath={base}',
        *example_files,
        os.path.join(base, 'gui.py'),
    ]

    print("Building EXE...")
    print(' '.join(cmd))
    result = subprocess.run(cmd, cwd=base)

    if result.returncode == 0:
        exe = os.path.join(base, 'dist', '16bit_Processor_Simulator.exe')
        print(f"\nSUCCESS!\nEXE: {exe}")
    else:
        print("\nBuild FAILED. Check output above.")
    return result.returncode

if __name__ == '__main__':
    sys.exit(main())