from __future__ import annotations

import csv
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIMULATOR = ROOT / "build" / "simulator"
PROGRAM = ROOT / "programs" / "momo_routine_nop_padded.hex"


def run_case(data_file: str) -> dict[str, str]:
    with tempfile.TemporaryDirectory() as directory:
        trace = Path(directory) / "trace.csv"
        subprocess.run(
            [
                str(SIMULATOR),
                str(PROGRAM),
                "--data",
                str(ROOT / "programs" / data_file),
                "--trace",
                str(trace),
                "--quiet",
            ],
            check=True,
            cwd=ROOT,
        )
        with trace.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        if not rows:
            raise AssertionError("simulator trace was empty")
        return rows[-1]


class PipelineIntegrationTests(unittest.TestCase):
    def test_accepted_transaction_updates_balance_and_flag(self) -> None:
        final = run_case("data_memory.hex")
        self.assertEqual(int(final["m0"]), 840)
        self.assertEqual(int(final["r8"]), 1)
        self.assertEqual((int(final["r9"]), int(final["r10"]), int(final["r11"])), (158, 156, 2))

    def test_limit_violation_preserves_balance_and_clears_flag(self) -> None:
        final = run_case("data_memory_reject.hex")
        self.assertEqual(int(final["m0"]), 1000)
        self.assertEqual(int(final["r8"]), 0)


if __name__ == "__main__":
    unittest.main()
