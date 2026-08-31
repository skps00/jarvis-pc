"""Compile-check listed jarvis/hermes Python files."""
import py_compile
import sys

PY = r"C:\Users\skps9\AppData\Local\Python\pythoncore-3.14-64\python.exe"
FILES = [
    r"C:\Users\skps9\Documents\Code_Project\jarvis-pc\src\jarvis\aec.py",
    r"C:\Users\skps9\Documents\Code_Project\jarvis-pc\src\jarvis\wake.py",
    r"C:\Users\skps9\AppData\Local\hermes\scripts\activity_monitor.py",
    r"C:\Users\skps9\Documents\Code_Project\jarvis-pc\src\jarvis\shell_app.py",
    r"C:\Users\skps9\Documents\Code_Project\jarvis-pc\src\jarvis\settings.py",
]

if __name__ == "__main__":
    overall = 0
    for f in FILES:
        print(f"=== {f} ===")
        try:
            py_compile.compile(f, doraise=True)
            print("exit_code=0")
        except py_compile.PyCompileError as e:
            overall = 1
            print(f"exit_code=1")
            print(e)
        except Exception as e:
            overall = 1
            print(f"exit_code=1")
            print(type(e).__name__, e)
    sys.exit(overall)
