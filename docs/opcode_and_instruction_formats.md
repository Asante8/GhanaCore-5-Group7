# GhanaCore-5 opcode and instruction-format table

Group 7, University of Ghana — Week 1 implementation artifact.

## Architectural encoding

Every instruction is one 32-bit word. The 6-bit opcode is always in `instruction[31:26]`; register identifiers are 4 bits and select one of sixteen registers (`r0`–`r15`). Register `r0` always reads as zero and ignores writes. The 18-bit immediate is signed two's-complement. Program-counter and data-memory addresses are **word addresses**, not byte addresses.

| Format | Bits 31:26 | Bits 25:22 | Bits 21:18 | Bits 17:14 | Bits 13:0 / 17:0 |
|---|---|---|---|---|---|
| R | `opcode[5:0]` | `rd[3:0]` | `rs1[3:0]` | `rs2[3:0]` | `reserved[13:0]=0` |
| I | `opcode[5:0]` | `rd[3:0]` | `rs1[3:0]` | part of `imm18` | `imm18 = instruction[17:0]` |
| S/B | `opcode[5:0]` | `rs2[3:0]` | `rs1[3:0]` | part of `imm18` | `imm18 = instruction[17:0]` |

For `LW`/`SW`, the effective word address is `R[rs1] + sign_extend(imm18)`. For branches, the target is `PC + 1 + sign_extend(imm18)`. A branch label is therefore assembled as `label_PC - (branch_PC + 1)`.

## Opcode table

| Mnemonic | Opcode (binary) | Hex | Format | Register/immediate meaning | Operation |
|---|:---:|:---:|:---:|---|---|
| `NOP` | `000000` | `0x00` | N | all remaining bits zero | No architectural change |
| `ADD` | `000001` | `0x01` | R | `rd, rs1, rs2` | `R[rd] = R[rs1] + R[rs2]` |
| `SUB` | `000010` | `0x02` | R | `rd, rs1, rs2` | `R[rd] = R[rs1] - R[rs2]` |
| `AND` | `000011` | `0x03` | R | `rd, rs1, rs2` | bitwise AND |
| `OR` | `000100` | `0x04` | R | `rd, rs1, rs2` | bitwise OR |
| `XOR` | `000101` | `0x05` | R | `rd, rs1, rs2` | bitwise XOR |
| `SLT` | `000110` | `0x06` | R | `rd, rs1, rs2` | signed less-than; result is 0 or 1 |
| `ADDI` | `001000` | `0x08` | I | `rd, rs1, imm18` | `R[rd] = R[rs1] + sign_extend(imm18)` |
| `LW` | `010000` | `0x10` | I | `rd, base=rs1, offset=imm18` | load one 32-bit word |
| `SW` | `010001` | `0x11` | S | `value=rs2, base=rs1, offset=imm18` | store one 32-bit word |
| `BEQ` | `011000` | `0x18` | B | `rs1, rs2, PC-relative imm18` | branch when equal |
| `BNE` | `011001` | `0x19` | B | `rs1, rs2, PC-relative imm18` | branch when not equal |

`0x07`, `0x09`–`0x0F`, `0x12`–`0x17`, and `0x1A`–`0x3F` are reserved and must make the control unit assert `Valid=0`.

## Exact decode slices used by IF/ID and ID

| Signal | Instruction slice | Width | Used by |
|---|:---:|---:|---|
| `opcode` | `[31:26]` | 6 | all instructions/control unit |
| `rd` | `[25:22]` | 4 | R, `ADDI`, `LW` |
| `rs2_or_store_branch` | `[25:22]` | 4 | `SW`, `BEQ`, `BNE` |
| `rs1` | `[21:18]` | 4 | R, I, S, B |
| `rs2_R` | `[17:14]` | 4 | R only |
| `imm18` | `[17:0]` | 18 | I, S, B; sign-extended to 32 bits in ID |

The authoritative executable definitions are `isa/isa.h` and `isa/isa.py`. The complete 18-word program and its generated binary are in `programs/momo_routine.s` and `docs/momo_routine_machine_code.md`.
