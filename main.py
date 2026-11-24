#!/usr/bin/env python3
"""news-image-20261124 — the entrypoint the grader runs.

v2: same copy-only entrypoint, press time 17:00 UTC. Standard library
only, and it only copies: the image itself is rendered at build time
by draw.py (Pillow) and committed as entry.png. Running this file
copies that PNG into the output directory and checks the copy is
byte-identical and a real 1024x1024 PNG.

Pass --verify to re-render from draw.py instead and confirm the
committed entry.png is exactly what the code draws.
"""
import hashlib
import os
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
IMAGE = ROOT / "entry.png"
MAGIC = b"\x89PNG\r\n\x1a\n"


def digest(path):
    """SHA-256 of a file, streamed in 1 MiB chunks."""
    total = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(1 << 20)
            if not chunk:
                break
            total.update(chunk)
    return total.hexdigest()


def render_check():
    """Re-render entry.png from draw.py in a temp dir and compare."""
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        shutil.copy(ROOT / "draw.py", work / "draw.py")
        shutil.copy(ROOT / "world.geo.json", work / "world.geo.json")
        done = subprocess.run([sys.executable, "draw.py"], cwd=work,
                              capture_output=True, text=True)
        if done.returncode != 0:
            print("draw.py failed:\n" + done.stderr, file=sys.stderr)
            return 1
        fresh = digest(work / "entry.png")
        kept = digest(IMAGE)
        if fresh != kept:
            print("render differs from committed entry.png: %s vs %s"
                  % (fresh, kept), file=sys.stderr)
            return 1
    print("verify: entry.png matches a fresh render (%s)" % fresh)
    return 0


def copy_out():
    """Copy entry.png to the output directory and check the copy."""
    if not IMAGE.is_file():
        print("missing source: %s" % IMAGE, file=sys.stderr)
        return 1
    if IMAGE.stat().st_size == 0:
        print("empty source: %s" % IMAGE, file=sys.stderr)
        return 1
    with open(IMAGE, "rb") as handle:
        head = handle.read(33)
    if head[:8] != MAGIC or head[12:16] != b"IHDR":
        print("source is not a PNG file: %s" % IMAGE, file=sys.stderr)
        return 1
    width, height = struct.unpack(">II", head[16:24])
    if (width, height) != (1024, 1024):
        print("source is %dx%d, expected 1024x1024" % (width, height),
              file=sys.stderr)
        return 1
    dest_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR")
                    or os.environ.get("OUTPUT_DIR") or "/output")
    dest_dir.mkdir(parents=True, exist_ok=True)
    target = dest_dir / "entry.png"
    shutil.copyfile(IMAGE, target)
    if digest(IMAGE) != digest(target):
        print("copy differs from source", file=sys.stderr)
        return 1
    os.chmod(target, 0o644)
    print("wrote %s (%d bytes, sha256 %s)"
          % (target, target.stat().st_size, digest(target)))
    return 0


def run(argv):
    if "--verify" in argv:
        return render_check()
    return copy_out()


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
