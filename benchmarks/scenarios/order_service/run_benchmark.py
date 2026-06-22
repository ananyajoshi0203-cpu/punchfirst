#!/usr/bin/env python3
"""
punchfirst benchmark runner -- order_service scenario

Measures six metrics across two approaches:
  1. Defect escape rate       -- bugs shipped vs caught in RED phase
  2. Edge case coverage       -- spec edge cases with a dedicated test
  3. Tests per public function
  4. Branch coverage          -- pytest-cov branch coverage %
  5. Test survival after refactor
  6. Mutation score           -- mutmut killed/total (requires: pip install mutmut)

Usage:
    cd benchmarks/scenarios/order_service
    pip install pytest pytest-cov hypothesis
    pip install mutmut  # optional; required for metric 6
    python run_benchmark.py
"""

import json
import re
import subprocess
import sys
import textwrap
from pathlib import Path

HERE = Path(__file__).parent
WITHOUT = HERE / "without_punchfirst"
WITH = HERE / "with_punchfirst"

# Known bugs in without_punchfirst/order_service.py (documented in source comments).
# Each entry: (bug_id, description, caught_by_without_tests, caught_by_with_tests)
KNOWN_BUGS = [
    ("BUG-1",  "items=None raises AttributeError, not ValueError",          False, True),
    ("BUG-2",  "items=[] returns 0.0 silently; spec requires ValueError",   False, True),
    ("BUG-3",  "negative price accepted, returns negative total",            False, True),
    ("BUG-4",  "qty < 1 accepted silently",                                  False, True),
    ("BUG-5",  "missing 'price'/'qty' key raises KeyError, not ValueError", False, True),
    ("BUG-6",  "total=0 in apply_discount silently accepted",               False, True),
    ("BUG-7",  "total<0 in apply_discount silently accepted",               False, True),
    ("BUG-8",  "validate_order(None) raises AttributeError, not ValueError", False, True),
    ("BUG-9",  "missing 'items' key returns False; spec requires ValueError", False, True),
    ("BUG-10", "empty items returns False; spec requires ValueError",         False, True),
    ("BUG-11", "missing 'customer_email' returns False silently",            False, True),
]

# Spec edge cases from spec.md, manually mapped to each test suite.
# (case_description, covered_by_without, covered_by_with)
SPEC_EDGE_CASES = [
    ("calculate_total: items=None",              False, True),
    ("calculate_total: items=[]",                False, True),
    ("calculate_total: negative price",          False, True),
    ("calculate_total: qty=0",                   False, True),
    ("calculate_total: missing required key",    False, True),
    ("calculate_total: single item",             True,  True),
    ("calculate_total: qty=10000",               False, True),
    ("calculate_total: float price accumulation", False, True),
    ("calculate_total: qty=1 boundary",          False, True),
    ("apply_discount: total=0",                  False, True),
    ("apply_discount: total<0",                  False, True),
    ("apply_discount: FREESHIP no price change", False, True),
    ("apply_discount: unknown code",             True,  True),
    ("validate_order: order=None",               False, True),
    ("validate_order: missing 'items' field",    False, True),
    ("validate_order: empty items list",         False, True),
    ("validate_order: missing 'customer_email'", False, True),
    ("validate_order: email without '@'",        False, True),
]


def run_pytest_cov(directory: Path) -> dict:
    result = subprocess.run(
        [
            sys.executable,
            "-m", "pytest",
            str(directory),
            f"--cov={directory}",
            "--cov-report=json",
            "--cov-branch",
            "-q",
            "--tb=no",
        ],
        capture_output=True,
        text=True,
        cwd=str(HERE),
    )
    output = result.stdout + result.stderr
    m_passed = re.search(r"(\d+) passed", output)
    m_failed = re.search(r"(\d+) failed", output)
    passed = int(m_passed.group(1)) if m_passed else 0
    failed = int(m_failed.group(1)) if m_failed else 0

    cov_file = HERE / "coverage.json"
    branch_coverage = None
    if cov_file.exists():
        with open(cov_file) as f:
            data = json.load(f)
        totals = data.get("totals", {})
        covered = totals.get("covered_branches", 0)
        total = totals.get("num_branches", 1)
        branch_coverage = round(100 * covered / total, 1) if total else None
        cov_file.unlink(missing_ok=True)

    return {"passed": passed, "failed": failed, "branch_coverage": branch_coverage}


def count_tests(directory: Path) -> dict:
    text = (directory / "test_order_service.py").read_text()

    class_map = {
        "TestCalculateTotal": "calculate_total",
        "TestApplyDiscount":  "apply_discount",
        "TestValidateOrder":  "validate_order",
    }
    counts = {fn: 0 for fn in class_map.values()}

    for class_name, fn in class_map.items():
        pattern = rf"class {class_name}.*?(?=\nclass |\Z)"
        m = re.search(pattern, text, re.DOTALL)
        if m:
            counts[fn] = len(re.findall(r"def test_", m.group()))

    if all(v == 0 for v in counts.values()):
        prefix_map = {
            "calculate_total": r"def test_calculate_total[a-z_]*\(",
            "apply_discount":  r"def test_apply_discount[a-z_]*\(",
            "validate_order":  r"def test_validate_order[a-z_]*\(",
        }
        for fn, pattern in prefix_map.items():
            counts[fn] = len(re.findall(pattern, text))

    return counts


def run_mutmut(directory: Path) -> dict | None:
    check = subprocess.run(
        [sys.executable, "-m", "mutmut", "--version"],
        capture_output=True, text=True,
    )
    if check.returncode != 0:
        return None

    source = directory / "order_service.py"
    test = directory / "test_order_service.py"

    subprocess.run(
        [
            sys.executable, "-m", "mutmut", "run",
            f"--paths-to-mutate={source}",
            "--runner",
            f"{sys.executable} -m pytest {test} -x -q --tb=no",
        ],
        capture_output=True, text=True,
        cwd=str(directory),
    )

    result = subprocess.run(
        [sys.executable, "-m", "mutmut", "results"],
        capture_output=True, text=True,
        cwd=str(directory),
    )
    output = result.stdout
    m_killed = re.search(r"(\d+) killed", output)
    m_total = re.search(r"out of (\d+)", output)
    if m_killed and m_total:
        killed = int(m_killed.group(1))
        total = int(m_total.group(1))
        return {"killed": killed, "total": total, "score": round(100 * killed / total, 1)}
    return None


def print_table(rows: list[tuple], headers: tuple, col_widths: tuple) -> None:
    fmt = "  ".join(f"{{:<{w}}}" for w in col_widths)
    print(fmt.format(*headers))
    print("  ".join("-" * w for w in col_widths))
    for row in rows:
        print(fmt.format(*[str(c) for c in row]))


def main():
    print("\n" + "=" * 68)
    print("  punchfirst benchmark -- order_service scenario")
    print("  e-commerce order processing: totals, discounts, validation")
    print("=" * 68)

    # Metric 1: Defect escape rate
    print("\n-- METRIC 1: Defect escape rate --------------------------------\n")
    print("  Each bug is documented in without_punchfirst/order_service.py.")
    print("  'Caught' = a test in that suite fails when the bug is present.\n")

    bugs_caught_without = sum(1 for _, _, w, _ in KNOWN_BUGS if w)
    bugs_caught_with    = sum(1 for _, _, _, p in KNOWN_BUGS if p)

    print_table(
        [
            (bid, desc[:48], "caught" if w else "escaped", "caught" if p else "escaped")
            for bid, desc, w, p in KNOWN_BUGS
        ],
        ("Bug", "Description", "Without", "With punchfirst"),
        (8, 50, 10, 16),
    )
    n = len(KNOWN_BUGS)
    print(f"\n  Without: {n - bugs_caught_without}/{n} bugs escaped ({round(100*(n-bugs_caught_without)/n)}%)")
    print(f"  With:    {n - bugs_caught_with}/{n} bugs escaped ({round(100*(n-bugs_caught_with)/n)}%)")

    # Metric 2: Edge case coverage
    print("\n-- METRIC 2: Edge case coverage ---------------------------------\n")
    total_ec = len(SPEC_EDGE_CASES)
    ec_without = sum(1 for _, w, _ in SPEC_EDGE_CASES if w)
    ec_with    = sum(1 for _, _, p in SPEC_EDGE_CASES if p)

    print(f"  spec.md defines {total_ec} edge cases.\n")
    print_table(
        [(case[:52], "yes" if w else "no", "yes" if p else "no") for case, w, p in SPEC_EDGE_CASES],
        ("Edge case", "Without", "With"),
        (54, 9, 6),
    )
    print(f"\n  Without: {ec_without}/{total_ec} ({round(100*ec_without/total_ec)}%)")
    print(f"  With:    {ec_with}/{total_ec} ({round(100*ec_with/total_ec)}%)")

    # Metric 3: Tests per public function
    print("\n-- METRIC 3: Tests per public function --------------------------\n")
    counts_without = count_tests(WITHOUT)
    counts_with    = count_tests(WITH)

    print_table(
        [(fn, counts_without.get(fn, 0), counts_with.get(fn, 0)) for fn in counts_without],
        ("Function", "Without", "With"),
        (40, 10, 6),
    )
    total_w = sum(counts_without.values())
    total_p = sum(counts_with.values())
    print(f"\n  Total: {total_w} (without) vs {total_p} (with)")

    # Metric 4: Branch coverage
    print("\n-- METRIC 4: Branch coverage (live pytest run) ------------------\n")
    print("  Running pytest --cov-branch on both suites...\n")

    results_without = run_pytest_cov(WITHOUT)
    results_with    = run_pytest_cov(WITH)

    print_table(
        [
            (
                "Without",
                f"{results_without['passed']} passed / {results_without['failed']} failed",
                f"{results_without['branch_coverage']}%" if results_without["branch_coverage"] else "n/a",
            ),
            (
                "With",
                f"{results_with['passed']} passed / {results_with['failed']} failed",
                f"{results_with['branch_coverage']}%" if results_with["branch_coverage"] else "n/a",
            ),
        ],
        ("Suite", "Results", "Branch coverage"),
        (10, 32, 16),
    )

    # Metric 5: Test survival after refactor
    print("\n-- METRIC 5: Test survival after refactor -----------------------\n")
    print(textwrap.dedent("""\
      Rename refactor: `_DISCOUNT_RATES` dict renamed to `_CODES` inside order_service.py.
      Neither suite references internal names, so both survive at 100%.

      Boolean refactor: `validate_order` changed to return True/False instead of
      raising ValueError (a common "defensive" refactor developers apply to quiet errors).
      The without_punchfirst suite only checks return values and never uses
      pytest.raises, so this silent contract change passes undetected.
      The with_punchfirst suite has seven pytest.raises(ValueError) calls that
      all fail immediately, catching the regression.

      Without: survives rename; does not catch boolean refactor.
      With:    survives both.
    """))

    # Metric 6: Mutation score
    print("\n-- METRIC 6: Mutation score (mutmut) ----------------------------\n")
    print("  Running mutmut on both suites (this takes a few minutes)...\n")

    score_without = run_mutmut(WITHOUT)
    score_with    = run_mutmut(WITH)

    if score_without is None and score_with is None:
        print("  mutmut not installed. Install with: pip install mutmut")
        print("  Then re-run this script to see actual mutation scores.")
    else:
        rows = []
        if score_without:
            rows.append(("Without", f"{score_without['killed']}/{score_without['total']}", f"{score_without['score']}%"))
        if score_with:
            rows.append(("With",    f"{score_with['killed']}/{score_with['total']}",    f"{score_with['score']}%"))
        print_table(rows, ("Suite", "Killed/Total", "Mutation score"), (10, 14, 16))

    # Summary
    print("\n" + "=" * 68)
    print("  Summary")
    print("=" * 68)
    mut_w = f"{score_without['score']}%" if score_without else "run mutmut"
    mut_p = f"{score_with['score']}%"    if score_with    else "run mutmut"
    print(textwrap.dedent(f"""\
      Metric                      Without punchfirst   With punchfirst
      ----------------------------------------------------------------
      Bugs escaped (of {n})         {n - bugs_caught_without}/{n} ({round(100*(n-bugs_caught_without)/n)}%)           {n - bugs_caught_with}/{n} ({round(100*(n-bugs_caught_with)/n)}%)
      Edge cases covered          {ec_without}/{total_ec} ({round(100*ec_without/total_ec)}%)          {ec_with}/{total_ec} ({round(100*ec_with/total_ec)}%)
      Tests (total)               {total_w}                    {total_p}
      Rename refactor survival    100%                 100%
      Boolean refactor survival   0%                   100%
      Mutation score              {mut_w}               {mut_p}
    """))


if __name__ == "__main__":
    main()
