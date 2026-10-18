#!/usr/bin/env python3
"""
PinkbikeDeals — launcher script.

Run this from any directory:
    python run.py          # Launch GUI
    python run.py scan     # CLI scan
    python run.py stats    # CLI stats
    python run.py --help   # Show all commands
"""

import sys
import os

# Add the project root to sys.path so 'src' is importable
# This works regardless of where the script is called from
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.main import main

if __name__ == "__main__":
    # If no arguments, default to GUI
    if len(sys.argv) == 1:
        sys.argv.append("gui")
    main()
