#!/usr/bin/env python3
"""
Entry point to run the Asteroids game.

Usage:
    python run.py
"""

import sys
from src.asteroids.main import main

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nGame closed.")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
