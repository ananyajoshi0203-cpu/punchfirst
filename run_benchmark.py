#!/usr/bin/env python3
"""
Run punchfirst benchmarks.

Usage:
    python run_benchmark.py                  # all scenarios
    python run_benchmark.py loan_service     # one scenario
    python run_benchmark.py order_service
"""

import subprocess
import sys
from pathlib import Path

SCENARIOS = ["loan_service", "order_service"]

base = Path(__file__).parent / "benchmarks" / "scenarios"
targets = sys.argv[1:] or SCENARIOS

for name in targets:
    script = base / name / "run_benchmark.py"
    if not script.exists():
        print(f"  [skip] {name}: no run_benchmark.py found")
        continue
    rc = subprocess.call([sys.executable, str(script)])
    if rc != 0:
        sys.exit(rc)
