"""Entry point for running outside of Briefcase (e.g. `python main.py`)."""

import sys
from pathlib import Path

# When running directly (not via Briefcase), add src/ to the path so that
# `lazy_fit` is importable.
sys.path.insert(0, str(Path(__file__).parent / "src"))

from lazy_fit.app import main  # noqa: E402

if __name__ == "__main__":
    main().main_loop()
