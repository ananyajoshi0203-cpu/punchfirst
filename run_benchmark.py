#!/usr/bin/env python3
"""Convenience wrapper -- runs the loan_service benchmark from the repo root."""

import subprocess
import sys
from pathlib import Path

script = Path(__file__).parent / "benchmarks" / "scenarios" / "loan_service" / "run_benchmark.py"
sys.exit(subprocess.call([sys.executable, str(script)]))
