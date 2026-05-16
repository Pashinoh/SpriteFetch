"""Create a release ZIP for SpriteFetch excluding development files.

Usage: run from tools folder with python, it writes ../releases/SpriteFetch-v0.1.zip
"""
import os
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT_DIR = os.path.join(ROOT, 'releases')
OUT_NAME = 'SpriteFetch-v0.1.zip'

EXCLUDE_DIRS = {'.git', '.venv', 'venv', '__pycache__', 'releases'}
EXCLUDE_FILES = {'.pyc', '.pyo'}

INCLUDE = {
    'app.py', 'README.md', 'requirements.txt', 'LICENSE'
}

def should_include(path):
    # include files explicitly listed, or everything except excluded dirs/files
    rel = os.path.relpath(path, ROOT)
    parts = rel.split(os.sep)
    if parts[0] in EXCLUDE_DIRS:
        return False
    if os.path.isdir(path):
        return True
    ext = os.path.splitext(path)[1]
    if ext in EXCLUDE_FILES:
        return False
    return True

def gather_files():
    files = []
    for root, dirs, filenames in os.walk(ROOT):
        # prune excluded dirs
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for fn in filenames:
            full = os.path.join(root, fn)
            # skip files in releases folder
            if not should_include(full):
                continue
            # include assets and docs if present
            rel = os.path.relpath(full, ROOT)
            files.append(rel)
    # ensure explicit includes are present
    for f in INCLUDE:
        if os.path.exists(os.path.join(ROOT, f)) and f not in files:
            files.append(f)
    return sorted(files)

def make_zip():
    os.makedirs(OUT_DIR, exist_ok=True)
    files = gather_files()
    out_path = os.path.join(OUT_DIR, OUT_NAME)
    with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(os.path.join(ROOT, f), arcname=f)
    print('Wrote', out_path)

if __name__ == '__main__':
    make_zip()
