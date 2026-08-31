import py_compile
import sys

for f in sys.argv[1:]:
    py_compile.compile(f, doraise=True)
    print(f"OK {f}")
