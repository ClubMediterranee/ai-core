#!/usr/bin/env python3
"""
Dependency checker and auto-installer for tracking-plan-render.
Exit 0 = all deps ready. Exit 1 = missing dep that cannot be installed.
"""

import argparse
import importlib
import subprocess
import sys

DEPS = {
    "excel":    [("openpyxl", "openpyxl>=3.1"), ("PIL", "pillow>=10.0")],
    "pdf":      [("reportlab", "reportlab>=4.0")],
    "markdown": [],
}

def check_and_install(module: str, package: str) -> bool:
    try:
        importlib.import_module(module)
        return True
    except ImportError:
        pass

    print(f"  Installing {package}...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", package, "-q"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        try:
            importlib.import_module(module)
            print(f"  ✓ {package} installed")
            return True
        except ImportError:
            pass

    print(f"\n❌ Could not install {package} automatically.")
    print(f"   Run manually: pip3 install {package}")
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--formats", default="excel,markdown,pdf",
                        help="Comma-separated list of formats to check")
    args = parser.parse_args()

    formats = [f.strip() for f in args.formats.split(",")]
    all_ok = True

    print("Checking dependencies...")
    for fmt in formats:
        deps = DEPS.get(fmt, [])
        if not deps:
            print(f"  ✓ {fmt} — no dependencies required")
            continue
        print(f"  {fmt}:")
        for module, package in deps:
            ok = check_and_install(module, package)
            if not ok:
                all_ok = False

    if all_ok:
        print("\n✓ All dependencies ready")
        sys.exit(0)
    else:
        print("\n❌ Some dependencies missing — install them manually (see above) then re-run")
        sys.exit(1)


if __name__ == "__main__":
    main()
