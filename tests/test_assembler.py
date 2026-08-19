from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from assembler.assembler import AssemblerError, assemble_file, assemble_lines
from isa.isa import Opcode, decode


class AssemblerTests(unittest.TestCase):
    def test_group7_routine_has_hand_computed_machine_words(self) -> None:
        assembled = assemble_file(ROOT / "programs" / "momo_routine.s")
        expected = [
            0x40400000,
            0x40800001,
            0x40C00002,
            0x41000003,
            0x0548C000,
            0x19908000,
            0x64180009,
            0x19C54000,
            0x641C0007,
            0x08454000,
            0x44400000,
            0x22000001,
            0x1248C000,
            0x1688C000,
            0x0EC8C000,
            0x60000001,
            0x22000000,
            0x00000000,
        ]
        self.assertEqual([item.word for item in assembled], expected)

    def test_two_pass_forward_and_backward_labels(self) -> None:
        assembled = assemble_lines(
            [
                "start: ADDI r1, r0, 1",
                "BEQ r1, r0, finish",
                "BNE r1, r0, start",
                "finish: NOP",
            ]
        )
        self.assertEqual(decode(assembled[1].word).immediate, 1)
        self.assertEqual(decode(assembled[2].word).immediate, -3)

    def test_all_required_instruction_classes_are_present(self) -> None:
        opcodes = {decode(item.word).opcode for item in assemble_file(ROOT / "programs" / "momo_routine.s")}
        self.assertTrue({Opcode.ADD, Opcode.ADDI, Opcode.BNE, Opcode.BEQ, Opcode.LW, Opcode.SW, Opcode.NOP} <= opcodes)

    def test_invalid_register_reports_source_error(self) -> None:
        with self.assertRaisesRegex(AssemblerError, "outside r0-r15"):
            assemble_lines(["ADD r16, r1, r2"])


if __name__ == "__main__":
    unittest.main()
