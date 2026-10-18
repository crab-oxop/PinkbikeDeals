#!/usr/bin/env python3
"""
PinkbikeDeals — Windows GUI launcher (no console window).

The .pyw extension tells Windows to use pythonw.exe which suppresses
the console window entirely. Double-click this file to launch.
"""

import sys
import os

# Add the project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.gui.app import main

if __name__ == "__main__":
    main()
