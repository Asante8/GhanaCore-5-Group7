# GhanaCore-5 pipeline-register construction specification

Group 7, University of Ghana — Week 2 Logisim handoff.

This is a build specification, not a conceptual sketch. Use four named Logisim subcircuits: `REG_IF_ID_65`, `REG_ID_EX_157`, `REG_EX_MEM_145`, and `REG_MEM_WB_77`. Each is a bank of positive-edge-triggered registers sharing `Clock`, synchronous active-high `Reset`, and active-high `Enable`. On `Reset=1`, every bit becomes zero. Normal execution holds `Enable=1`; a flush writes `Valid=0` into the younger register while the other data bits may be don't-care.

The machine uses word-addressed 32-bit `PC`. The ID stage sign-extends `instruction[17:0]` to a 32-bit `Immediate`. Control bits originate in `ControlUnit` and move only as far as they are needed.

## `REG_IF_ID_65` — 65 bits

| Packed bits | Width | Logisim signal | Producer → consumer | Meaning |
|:---:|---:|---|---|---|
| `[64]` | 1 | `IFID_Valid` | IF → ID | 1 for a real instruction; 0 for bubble |
| `[63:32]` | 32 | `IFID_PC` | PC → branch-offset logic/debug | word address of instruction |
| `[31:0]` | 32 | `IFID_Instruction` | instruction ROM → decoder | complete encoded word |

The decoder takes `IFID_Instruction[31:26]` as `Opcode`, `[25:22]` as `RdOrRs2`, `[21:18]` as `Rs1`, `[17:14]` as R-format `Rs2`, and `[17:0]` as `Imm18`.

## `REG_ID_EX_157` — 157 bits

| Packed bits | Width | Logisim signal | Producer → consumer | Meaning |
|:---:|---:|---|---|---|
| `[156]` | 1 | `IDEX_Valid` | ID → EX | instruction/bubble marker |
| `[155:124]` | 32 | `IDEX_PC` | IF/ID → branch adder | instruction word address |
| `[123:92]` | 32 | `IDEX_Rs1Value` | register-file port A → ALU/compare |
| `[91:60]` | 32 | `IDEX_Rs2Value` | register-file port B → ALU/store/compare |
| `[59:28]` | 32 | `IDEX_Immediate` | sign extender → ALU/branch adder |
| `[27:24]` | 4 | `IDEX_Rd` | decoder → destination path | R/I destination; 0 for S/B |
| `[23:20]` | 4 | `IDEX_Rs1` | decoder → debug/hazard probes | source 1 identifier |
| `[19:16]` | 4 | `IDEX_Rs2` | decoder → debug/hazard probes | source 2/store-data identifier |
| `[15:10]` | 6 | `IDEX_Opcode` | decoder → trace/probes | original opcode |
| `[9]` | 1 | `IDEX_RegWrite` | control → EX/MEM | write destination register later |
| `[8]` | 1 | `IDEX_MemRead` | control → EX/MEM | read data memory |
| `[7]` | 1 | `IDEX_MemWrite` | control → EX/MEM | write data memory |
| `[6]` | 1 | `IDEX_MemToReg` | control → EX/MEM | select loaded value at WB |
| `[5]` | 1 | `IDEX_ALUSrcImm` | control → ALU B mux | 1 selects immediate; 0 selects Rs2 |
| `[4]` | 1 | `IDEX_Branch` | control → branch decision | opcode is a branch |
| `[3]` | 1 | `IDEX_BranchNE` | control → branch decision | invert equality for BNE |
| `[2:0]` | 3 | `IDEX_ALUOp` | control → ALU | encoding from control table |

For S/B instructions, ID routes `instruction[25:22]` into `IDEX_Rs2`; for R instructions it routes `instruction[17:14]`. For `SW`, `IDEX_Rs2Value` is the value eventually stored.

## `REG_EX_MEM_145` — 145 bits

| Packed bits | Width | Logisim signal | Producer → consumer | Meaning |
|:---:|---:|---|---|---|
| `[144]` | 1 | `EXMEM_Valid` | EX → MEM | instruction/bubble marker |
| `[143:112]` | 32 | `EXMEM_PC` | ID/EX → debug | originating PC |
| `[111:106]` | 6 | `EXMEM_Opcode` | ID/EX → trace/probes | original opcode |
| `[105:74]` | 32 | `EXMEM_ALUResult` | ALU → data address/WB | arithmetic result or word address |
| `[73:42]` | 32 | `EXMEM_StoreData` | ID/EX Rs2 value → data RAM | data written by SW |
| `[41:38]` | 4 | `EXMEM_Rd` | ID/EX Rd → MEM/WB | destination register |
| `[37]` | 1 | `EXMEM_CompareEqual` | EX comparator → probe | `Rs1Value == Rs2Value` |
| `[36]` | 1 | `EXMEM_BranchTaken` | branch logic → PC/flush | resolved decision |
| `[35:4]` | 32 | `EXMEM_BranchTarget` | `PC + 1 + Immediate` → PC | target word address |
| `[3]` | 1 | `EXMEM_RegWrite` | ID/EX control → MEM/WB |
| `[2]` | 1 | `EXMEM_MemRead` | ID/EX control → data RAM read-enable |
| `[1]` | 1 | `EXMEM_MemWrite` | ID/EX control → data RAM write-enable |
| `[0]` | 1 | `EXMEM_MemToReg` | ID/EX control → MEM/WB |

`BranchTaken = IDEX_Branch AND (IDEX_BranchNE XOR CompareEqual)`. When it is 1, set `PC = EXMEM_BranchTarget` and write zero to both `IFID_Valid` and `IDEX_Valid`. These are the two younger wrong-path instructions.

## `REG_MEM_WB_77` — 77 bits

| Packed bits | Width | Logisim signal | Producer → consumer | Meaning |
|:---:|---:|---|---|---|
| `[76]` | 1 | `MEMWB_Valid` | MEM → WB | instruction/bubble marker |
| `[75:70]` | 6 | `MEMWB_Opcode` | EX/MEM → trace/probes | original opcode |
| `[69:38]` | 32 | `MEMWB_MemoryData` | data RAM → WB mux | loaded word |
| `[37:6]` | 32 | `MEMWB_ALUResult` | EX/MEM → WB mux | non-load result |
| `[5:2]` | 4 | `MEMWB_Rd` | EX/MEM → register file | destination register |
| `[1]` | 1 | `MEMWB_RegWrite` | EX/MEM control → register-file WE |
| `[0]` | 1 | `MEMWB_MemToReg` | EX/MEM control → WB mux select |

The WB mux output is `MEMWB_MemToReg ? MEMWB_MemoryData : MEMWB_ALUResult`. Register-file write enable is `MEMWB_Valid AND MEMWB_RegWrite`. Writes to `r0` are ignored. Clock the register-file write early enough that the ID-stage combinational reads see that value during the same architectural cycle; the C simulator models WB before ID reads.

## Required top-level subcircuit and probes

Create top-level circuit `GhanaCore5` containing `PC32`, `InstructionROM32`, `ControlUnit`, `RegisterFile16x32_2R1W`, `ALU32`, `DataRAM256x32`, the four pipeline-register subcircuits, and a `BranchFlush` block. Expose probes named `PC`, `IFID_Instruction`, `IDEX_Opcode`, `EXMEM_ALUResult`, `MEMWB_WriteData`, `RegWrite`, `MemWrite`, and `BranchTaken` so the Logisim run can be compared directly with the simulator CSV trace.

There is no forwarding and no automatic data-hazard interlock in this baseline. Use `programs/momo_routine_nop_padded.hex`; NOPs are software-visible encoded zero words. Taken branches are handled by the EX-stage two-instruction flush, so the two sequential words after a branch need not be architectural delay slots.
