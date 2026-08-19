# assembler/ (placeholder — Week 2+)

Will turn MoMo assembly source (`.momo`/`.s` files) into GhanaCore-5 machine
code, using the encoding rules and `OPCODE`/`FUNCT` tables already defined
in [`../isa/isa.py`](../isa/isa.py). The `Instr`/`assemble()` machinery in
`isa.py` (label resolution, R/I/J encoding) is the starting point — Week 2
work is a real two-pass assembler with a text syntax, a `.s` -> `.bin`/`.hex`
CLI, and error reporting, rather than Python-embedded instruction lists.
