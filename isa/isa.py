"""
GhanaCore-5 Instruction Set Architecture (Week 1 draft)
Group 7 -- CPEN 438 Project 2, University of Ghana

GhanaCore-5 is a 32-bit, fixed-width, load/store instruction set built for a
five-stage pipelined processor (IF, ID, EX, MEM, WB) that executes mobile-money
(MoMo) transaction routines: balance checks, fee/limit arithmetic, and
balance load/store.

This file is the single source of truth for the encoding: opcode / funct
values, register numbering, the three instruction formats, an encoder, a
disassembler, and the actual assembled MoMo routine used as our Week 1
worked example (see momo_routine() and __main__ below).

Word size        : 32 bits
Registers         : 16 general-purpose registers, R0 hardwired to 0
Byte addressing   : memory is byte-addressed; LW/SW use word-aligned addresses
Branch semantics  : PC-relative. target = (index_of_branch + 1) + imm  (imm in words)
Jump semantics    : absolute. target = imm (word address), no shifting
Signedness        : all immediate/offset fields are 18-bit two's complement
"""

from dataclasses import dataclass, field
from typing import Optional

# ---------------------------------------------------------------------------
# 1. Register file
# ---------------------------------------------------------------------------
# 16 registers, 4-bit register fields. R0 is hardwired to zero (like MIPS $zero).
REGISTERS = {
    "zero": 0,   # hardwired 0 -- writes are discarded
    "bal":  1,   # account balance (loaded from / stored to memory)
    "amt":  2,   # transaction amount
    "fee":  3,   # transaction fee
    "lim":  4,   # transaction / balance limit (bounds-check threshold)
    "adr":  5,   # scratch: memory address of balance word
    "t0":   6,   # temporary
    "t1":   7,   # temporary
    "t2":   8,   # temporary
    "t3":   9,   # temporary
    "t4":   10,  # temporary
    "t5":   11,  # temporary
    "t6":   12,  # temporary
    "t7":   13,  # temporary
    "ra":   14,  # return address (JAL/JR)
    "sp":   15,  # stack pointer (reserved, unused in Week 1 routine)
}
REG_NAME_BY_NUM = {v: f"${k}" for k, v in REGISTERS.items()}
REG_BITS = 4          # 16 registers -> 4 bits
IMM_BITS = 18          # I-type immediate/offset width
ADDR_BITS = 26          # J-type absolute word-address width
WORD_BITS = 32

# ---------------------------------------------------------------------------
# 2. Instruction formats
# ---------------------------------------------------------------------------
# R-type : opcode(6) | rs(4) | rt(4) | rd(4) | unused(8) | funct(6)   = 32 bits
# I-type : opcode(6) | rs(4) | rt(4) | imm(18)                       = 32 bits
# J-type : opcode(6) | addr(26)                                      = 32 bits
FORMATS = ("R", "I", "J")

# ---------------------------------------------------------------------------
# 3. Opcode / funct table  (this IS the opcode/format source of truth --
#    docs/opcode_format_table.md is generated to match these exact values)
# ---------------------------------------------------------------------------
OPCODE = {
    # R-type instructions all share opcode 000000; funct selects the operation.
    "ADD":  0b000000,
    "SUB":  0b000000,
    "AND":  0b000000,
    "OR":   0b000000,
    "XOR":  0b000000,
    "SLT":  0b000000,
    "JR":   0b000000,
    "NOP":  0b000000,
    # I-type
    "ADDI": 0b001000,
    "SUBI": 0b001001,
    "ANDI": 0b001100,
    "ORI":  0b001101,
    "SLTI": 0b001010,
    "LUI":  0b001111,
    "LW":   0b100011,
    "SW":   0b101011,
    "BEQ":  0b000100,
    "BNE":  0b000101,
    # J-type
    "J":    0b000010,
    "JAL":  0b000011,
}

FUNCT = {
    "ADD": 0b100000,
    "SUB": 0b100010,
    "AND": 0b100100,
    "OR":  0b100101,
    "XOR": 0b100110,
    "SLT": 0b101010,
    "JR":  0b001000,
    "NOP": 0b111111,   # all-zero operand fields distinguish this from ADD $0,$0,$0
}

FORMAT_OF = {
    "ADD": "R", "SUB": "R", "AND": "R", "OR": "R", "XOR": "R",
    "SLT": "R", "JR": "R", "NOP": "R",
    "ADDI": "I", "SUBI": "I", "ANDI": "I", "ORI": "I", "SLTI": "I",
    "LUI": "I", "LW": "I", "SW": "I", "BEQ": "I", "BNE": "I",
    "J": "J", "JAL": "J",
}

# Which fields each pipeline stage actually needs the instruction for
# (used to cross-check docs/opcode_format_table.md against this file).
USES_RS  = {"ADD","SUB","AND","OR","XOR","SLT","JR","ADDI","SUBI","ANDI","ORI","SLTI","LW","SW","BEQ","BNE"}
USES_RT  = {"ADD","SUB","AND","OR","XOR","SLT","ADDI","SUBI","ANDI","ORI","SLTI","LUI","LW","SW","BEQ","BNE"}
USES_RD  = {"ADD","SUB","AND","OR","XOR","SLT"}
USES_IMM = {"ADDI","SUBI","ANDI","ORI","SLTI","LUI","LW","SW","BEQ","BNE"}
IS_BRANCH = {"BEQ","BNE"}
IS_JUMP   = {"J","JAL"}
IS_MEM_READ  = {"LW"}
IS_MEM_WRITE = {"SW"}
WRITES_REG_R = {"ADD","SUB","AND","OR","XOR","SLT"}          # writes rd
WRITES_REG_I = {"ADDI","SUBI","ANDI","ORI","SLTI","LUI","LW"}  # writes rt
WRITES_REG_J = {"JAL"}                                         # writes $ra


def _u(value: int, bits: int) -> int:
    """Mask a (possibly negative, two's-complement) value to `bits` bits."""
    return value & ((1 << bits) - 1)


def reg(name: str) -> int:
    name = name.lstrip("$")
    if name not in REGISTERS:
        raise ValueError(f"unknown register '${name}'")
    return REGISTERS[name]


# ---------------------------------------------------------------------------
# 4. Encoder
# ---------------------------------------------------------------------------
def encode_r(mnem: str, rd: str = "zero", rs: str = "zero", rt: str = "zero") -> int:
    opcode = OPCODE[mnem]
    funct = FUNCT[mnem]
    word = opcode << 26
    word |= reg(rs) << 22
    word |= reg(rt) << 18
    word |= reg(rd) << 14
    # bits [13:6] are unused/reserved in this ISA (8 bits)
    word |= funct
    return _u(word, WORD_BITS)


def encode_i(mnem: str, rt: str = "zero", rs: str = "zero", imm: int = 0) -> int:
    opcode = OPCODE[mnem]
    word = opcode << 26
    word |= reg(rs) << 22
    word |= reg(rt) << 18
    word |= _u(imm, IMM_BITS)
    return _u(word, WORD_BITS)


def encode_j(mnem: str, addr: int = 0) -> int:
    opcode = OPCODE[mnem]
    word = opcode << 26
    word |= _u(addr, ADDR_BITS)
    return _u(word, WORD_BITS)


@dataclass
class Instr:
    """One assembly-level instruction, plus an optional label it defines."""
    mnem: str
    rd: Optional[str] = None
    rs: Optional[str] = None
    rt: Optional[str] = None
    imm: Optional[int] = None
    label: Optional[str] = None   # label this instruction's address resolves to
    target: Optional[str] = None  # label this instruction branches/jumps to

    def fmt(self) -> str:
        return FORMAT_OF[self.mnem]


def assemble(program: list) -> list:
    """
    Resolve labels and encode a list of Instr into 32-bit machine words.
    Branch immediates are PC-relative in words: target = (index + 1) + imm.
    Jump addresses are absolute word indices.
    """
    labels = {ins.label: idx for idx, ins in enumerate(program) if ins.label}

    words = []
    for idx, ins in enumerate(program):
        m = ins.mnem
        if ins.target is not None:
            if m in IS_BRANCH:
                imm = labels[ins.target] - (idx + 1)
                words.append(encode_i(m, rt=ins.rt, rs=ins.rs, imm=imm))
            elif m in IS_JUMP:
                words.append(encode_j(m, addr=labels[ins.target]))
            else:
                raise ValueError(f"instruction {m} cannot take a label target")
        elif ins.fmt() == "R":
            words.append(encode_r(m, rd=ins.rd or "zero", rs=ins.rs or "zero", rt=ins.rt or "zero"))
        elif ins.fmt() == "I":
            words.append(encode_i(m, rt=ins.rt or "zero", rs=ins.rs or "zero", imm=ins.imm or 0))
        elif ins.fmt() == "J":
            words.append(encode_j(m, addr=ins.imm or 0))
    return words


# ---------------------------------------------------------------------------
# 5. Week 1 worked example: MoMo debit routine
#    - arithmetic checks : ADD, SUB, SLT
#    - immediate ops     : ADDI (x4)
#    - one bounds-check branch : SLT + BNE (insufficient-funds check)
#    - one load/store of balance : LW / SW
#    - control flow      : J, NOP
#
#    C-like pseudocode:
#       adr = 0x040                 // address of balance word in data memory
#       bal = MEM[adr]              // load balance
#       amt = 50; fee = 2
#       t0  = amt + fee             // total debit
#       t1  = (bal < t0) ? 1 : 0    // bounds check: insufficient funds?
#       if (t1 != 0) goto INSUFFICIENT
#       bal = bal - t0              // apply debit
#       lim = 5000                  // balance ceiling (AML cap check pattern)
#       t2  = (lim < bal) ? 1 : 0   // over-cap check (recorded, not branched on in Wk1)
#       MEM[adr] = bal              // store updated balance
#       goto DONE
#   INSUFFICIENT:
#       t0 = -1                     // error code: insufficient funds
#   DONE:
#       nop
# ---------------------------------------------------------------------------
def momo_routine() -> list:
    return [
        Instr("ADDI", rt="adr", rs="zero", imm=0x040),
        Instr("LW",   rt="bal", rs="adr",  imm=0),
        Instr("ADDI", rt="amt", rs="zero", imm=50),
        Instr("ADDI", rt="fee", rs="zero", imm=2),
        Instr("ADD",  rd="t0",  rs="amt",  rt="fee"),
        Instr("SLT",  rd="t1",  rs="bal",  rt="t0"),
        Instr("BNE",  rs="t1",  rt="zero", target="INSUFFICIENT"),
        Instr("SUB",  rd="bal", rs="bal",  rt="t0"),
        Instr("ADDI", rt="lim", rs="zero", imm=5000),
        Instr("SLT",  rd="t2",  rs="lim",  rt="bal"),
        Instr("SW",   rt="bal", rs="adr",  imm=0),
        Instr("J",    target="DONE"),
        Instr("ADDI", rt="t0",  rs="zero", imm=-1, label="INSUFFICIENT"),
        Instr("NOP",  label="DONE"),
    ]


def disassemble_line(ins: Instr) -> str:
    m = ins.mnem
    if m == "NOP":
        return "nop"
    if m in ("ADD", "SUB", "AND", "OR", "XOR", "SLT"):
        return f"{m.lower():<5} ${ins.rd}, ${ins.rs}, ${ins.rt}"
    if m == "JR":
        return f"{m.lower():<5} ${ins.rs}"
    if m in ("ADDI", "SUBI", "ANDI", "ORI", "SLTI"):
        return f"{m.lower():<5} ${ins.rt}, ${ins.rs}, {ins.imm}"
    if m == "LUI":
        return f"{m.lower():<5} ${ins.rt}, {ins.imm}"
    if m in ("LW", "SW"):
        return f"{m.lower():<5} ${ins.rt}, {ins.imm}(${ins.rs})"
    if m in ("BEQ", "BNE"):
        tgt = ins.target if ins.target else ins.imm
        return f"{m.lower():<5} ${ins.rs}, ${ins.rt}, {tgt}"
    if m in ("J", "JAL"):
        tgt = ins.target if ins.target else ins.imm
        return f"{m.lower():<5} {tgt}"
    return m.lower()


if __name__ == "__main__":
    program = momo_routine()
    words = assemble(program)

    print(f"{'#':>3}  {'label':<13} {'assembly':<32} {'hex':<10} binary")
    print("-" * 100)
    for idx, (ins, w) in enumerate(zip(program, words)):
        label = f"{ins.label}:" if ins.label else ""
        addr = idx * 4
        print(f"{addr:>3}  {label:<13} {disassemble_line(ins):<32} "
              f"0x{w:08X}  {w:032b}")
