# simulator/ (placeholder — Week 2+)

Will hold a cycle-accurate simulator of the GhanaCore-5 five-stage pipeline
(IF, ID, EX, MEM, WB), driven by the machine code produced by
[`../assembler/`](../assembler/) and decoded per
[`../docs/opcode_format_table.md`](../docs/opcode_format_table.md). Planned
scope: pipeline register state per cycle, data hazard detection/forwarding,
load-use stalls, and branch resolution — verified against the Week 1
[MoMo debit routine](../docs/momo_routine.md) as the first test program.
