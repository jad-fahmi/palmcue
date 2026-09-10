"""Frozen entry point: divert multiprocessing children before importing Qt."""

import multiprocessing
import sys

if __name__ == "__main__":
    multiprocessing.freeze_support()
    if "--self-test" in sys.argv:
        from pathlib import Path

        from palmcue.selftest import run

        report = Path(sys.argv[sys.argv.index("--self-test") + 1])
        sys.exit(run(report, camera="--camera" in sys.argv))
    from palmcue.app import main

    main()
