# GhanaCore-5 combinational control truth table

Group 7, University of Ghana — Week 2 implementation artifact.

The Logisim subcircuit `ControlUnit` takes `opcode[5:0]` and emits the following signals with no clocked state. The C implementation is `simulator/control_unit.h`; the equivalent executable Python mapping is `simulator/control_unit.py`.

| Opcode | Hex | Valid | RegWrite | MemRead | MemWrite | MemToReg | ALUSrcImm | Branch | BranchNE | ALUOp[2:0] |
|---|:---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| NOP | `00` | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | PASS `110` |
| ADD | `01` | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | ADD `000` |
| SUB | `02` | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | SUB `001` |
| AND | `03` | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | AND `010` |
| OR | `04` | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | OR `011` |
| XOR | `05` | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | XOR `100` |
| SLT | `06` | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | SLT `101` |
| ADDI | `08` | 1 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | ADD `000` |
| LW | `10` | 1 | 1 | 1 | 0 | 1 | 1 | 0 | 0 | ADD `000` |
| SW | `11` | 1 | 0 | 0 | 1 | 0 | 1 | 0 | 0 | ADD `000` |
| BEQ | `18` | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | SUB `001` |
| BNE | `19` | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | SUB `001` |
| all reserved opcodes | — | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | PASS `110` |

## Logisim implementation rule

Build the mapping as a ROM with a 6-bit address and an 11-bit data word, or as a combinational decoder. If a ROM is used, pack the output as:

```text
control_word[10:0] = {Valid, RegWrite, MemRead, MemWrite,
                      MemToReg, ALUSrcImm, Branch, BranchNE,
                      ALUOp[2:0]}
```

The pipeline does not carry `Valid` from the control word; each pipeline register has its own bubble-valid bit. An unsupported opcode stops the simulator and should light an `IllegalOpcode` probe in Logisim.

Branch resolution occurs in EX. `BranchNE=0` selects equality for `BEQ`; `BranchNE=1` inverts the equality result for `BNE`. `MemRead` and `MemWrite` use the ALU result as a **word address**.
