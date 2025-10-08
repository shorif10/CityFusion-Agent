#!/usr/bin/env python3
"""
CityFusion-Agent - Real-time city insights through intelligent agents.

This script provides a convenient entry point for running the application.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.main import main

if __name__ == "__main__":
    main()