from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from isa.isa import Opcode
from simulator.control_unit import AluOp, control_for_opcode


class ControlUnitTests(unittest.TestCase):
    def test_every_opcode_matches_independent_expected_tuple(self) -> None:
        # Tuple order: RegWrite, MemRead, MemWrite, MemToReg,
        # ALUSrcImm, Branch, BranchNE, ALUOp.
        expected = {
            Opcode.NOP:  (0, 0, 0, 0, 0, 0, 0, AluOp.PASS),
            Opcode.ADD:  (1, 0, 0, 0, 0, 0, 0, AluOp.ADD),
            Opcode.SUB:  (1, 0, 0, 0, 0, 0, 0, AluOp.SUB),
            Opcode.AND:  (1, 0, 0, 0, 0, 0, 0, AluOp.AND),
            Opcode.OR:   (1, 0, 0, 0, 0, 0, 0, AluOp.OR),
            Opcode.XOR:  (1, 0, 0, 0, 0, 0, 0, AluOp.XOR),
            Opcode.SLT:  (1, 0, 0, 0, 0, 0, 0, AluOp.SLT),
            Opcode.ADDI: (1, 0, 0, 0, 1, 0, 0, AluOp.ADD),
            Opcode.LW:   (1, 1, 0, 1, 1, 0, 0, AluOp.ADD),
            Opcode.SW:   (0, 0, 1, 0, 1, 0, 0, AluOp.ADD),
            Opcode.BEQ:  (0, 0, 0, 0, 0, 1, 0, AluOp.SUB),
            Opcode.BNE:  (0, 0, 0, 0, 0, 1, 1, AluOp.SUB),
        }
        for opcode, wanted in expected.items():
            with self.subTest(opcode=opcode.name):
                actual = control_for_opcode(opcode)
                got = (
                    actual.reg_write,
                    actual.mem_read,
                    actual.mem_write,
                    actual.mem_to_reg,
                    actual.alu_src_imm,
                    actual.branch,
                    actual.branch_not_equal,
                    actual.alu_op,
                )
                self.assertEqual(got, wanted)

    def test_reserved_opcode_is_rejected(self) -> None:
        with self.assertRaises(KeyError):
            control_for_opcode(0x3F)


if __name__ == "__main__":
    unittest.main()
