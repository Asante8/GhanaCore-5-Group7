"""Executable opcode-to-control mapping matching control_unit.h."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from isa.isa import Opcode


class AluOp(IntEnum):
    ADD = 0
    SUB = 1
    AND = 2
    OR = 3
    XOR = 4
    SLT = 5
    PASS = 6


@dataclass(frozen=True)
class ControlSignals:
    reg_write: int = 0
    mem_read: int = 0
    mem_write: int = 0
    mem_to_reg: int = 0
    alu_src_imm: int = 0
    branch: int = 0
    branch_not_equal: int = 0
    alu_op: AluOp = AluOp.PASS


CONTROL_TABLE: dict[Opcode, ControlSignals] = {
    Opcode.NOP: ControlSignals(),
    Opcode.ADD: ControlSignals(reg_write=1, alu_op=AluOp.ADD),
    Opcode.SUB: ControlSignals(reg_write=1, alu_op=AluOp.SUB),
    Opcode.AND: ControlSignals(reg_write=1, alu_op=AluOp.AND),
    Opcode.OR: ControlSignals(reg_write=1, alu_op=AluOp.OR),
    Opcode.XOR: ControlSignals(reg_write=1, alu_op=AluOp.XOR),
    Opcode.SLT: ControlSignals(reg_write=1, alu_op=AluOp.SLT),
    Opcode.ADDI: ControlSignals(reg_write=1, alu_src_imm=1, alu_op=AluOp.ADD),
    Opcode.LW: ControlSignals(reg_write=1, mem_read=1, mem_to_reg=1, alu_src_imm=1, alu_op=AluOp.ADD),
    Opcode.SW: ControlSignals(mem_write=1, alu_src_imm=1, alu_op=AluOp.ADD),
    Opcode.BEQ: ControlSignals(branch=1, alu_op=AluOp.SUB),
    Opcode.BNE: ControlSignals(branch=1, branch_not_equal=1, alu_op=AluOp.SUB),
}


def control_for_opcode(opcode: Opcode | int) -> ControlSignals:
    try:
        normalized = Opcode(opcode)
    except ValueError as exc:
        raise KeyError(f"unsupported opcode 0x{int(opcode):02X}") from exc
    return CONTROL_TABLE[normalized]


def main() -> None:
    print("| Opcode | Hex | RegWrite | MemRead | MemWrite | MemToReg | ALUSrcImm | Branch | BranchNE | ALUOp |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|---|")
    for opcode in Opcode:
        signals = control_for_opcode(opcode)
        print(
            f"| {opcode.name} | 0x{int(opcode):02X} | {signals.reg_write} | {signals.mem_read} | "
            f"{signals.mem_write} | {signals.mem_to_reg} | {signals.alu_src_imm} | "
            f"{signals.branch} | {signals.branch_not_equal} | {signals.alu_op.name} ({int(signals.alu_op):03b}) |"
        )


if __name__ == "__main__":
    main()
