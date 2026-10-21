# -*- coding: utf-8 -*-
"""Упаковка лабораторной работы в zip для Visual Studio (report/make_zip.py)."""
import os
import zipfile

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(BASE, ".."))
OUT = os.path.join(os.path.dirname(ROOT), "Lab_WebAPI_Skosar_AS-23-04.zip")
SKIP_DIRS = {"bin", "obj", ".vs", ".idea", "node_modules", "__pycache__", "out"}

count = 0
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in sorted(filenames):
            full = os.path.join(dirpath, fn)
            z.write(full, os.path.relpath(full, os.path.dirname(ROOT)))
            count += 1
print("files:", count, "->", OUT, os.path.getsize(OUT), "bytes")
