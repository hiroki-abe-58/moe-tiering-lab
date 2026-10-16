#!/usr/bin/env python3
"""Print the error lines of an MSVC/nvcc/ninja log captured by `cmd /c ... *> log` (PowerShell writes UTF-16)."""
import re
import sys

b = open(sys.argv[1], "rb").read()
t = b.decode("utf-16", errors="replace") if b[:2] in (b"\xff\xfe", b"\xfe\xff") else b.decode("utf-16-le", errors="replace") if b"\x00" in b[:200] else b.decode("utf-8", errors="replace")
for line in t.splitlines():
    if re.search(r"\berror\b|FAILED|CMake Error|fatal", line):
        print(line[:300])
