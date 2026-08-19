# Week 1 paper-review slides — RISC foundations and GhanaCore-5

Group 7 · CPEN 438 Project 2 · University of Ghana

The text below is ready to paste into presentation software. Each section is one slide; the speaker notes are a complete talk track rather than instructions to the presenter.

---

## Slide 1 — From the RISC argument to GhanaCore-5

**On-slide text**

**Two papers, one design question:** how much processor complexity actually helps programs run efficiently?

- David A. Patterson & David R. Ditzel, “The Case for the Reduced Instruction Set Computer” (1980)
- David A. Patterson & Carlo H. Séquin, “RISC I: A Reduced Instruction Set VLSI Computer” (1981)
- Group 7 review: implications for a fixed-width, five-stage MoMo processor

**Speaker notes**

Our review follows an argument and then its implementation. The 1980 paper challenges the assumption that adding more elaborate instructions always improves a computer. The 1981 paper turns that challenge into RISC I, a concrete VLSI processor. We finish by identifying which ideas we adopted in GhanaCore-5 and which simplifications are specific to our course prototype.

Primary sources: [1980 ACM record](https://dl.acm.org/doi/10.1145/641914.641917); [1981 RISC I paper](https://people.eecs.berkeley.edu/~sequin/X/CCD_RISC_VLSI/RISC1_Patterson_Sequin_1981.pdf).

---

## Slide 2 — The context: why complex instruction sets looked attractive

**On-slide text**

- Memory was expensive, so dense machine code mattered.
- Designers tried to close the “semantic gap” between high-level languages and machine instructions.
- Rich instructions promised fewer instructions per program.
- Microcode made complicated instruction behavior practical to implement.

**The question raised in 1980:** does reducing the dynamic instruction count compensate for slower, harder-to-design instructions and control?

**Speaker notes**

Complex instruction sets were not irrational. They responded to real cost pressures and to the growing use of high-level languages. Patterson and Ditzel ask us to evaluate the whole system, however: instruction frequency, control complexity, implementation time, compiler behavior, and execution time. A single powerful instruction is not automatically a win if it is rarely used or lengthens the path for common operations.

Source: [Patterson & Ditzel, 1980](https://dl.acm.org/doi/10.1145/641914.641917).

---

## Slide 3 — Patterson & Ditzel (1980): central thesis

**On-slide text**

**Central claim:** a smaller set of simple, frequently used instructions can yield a better overall computer than a growing set of complex, specialized instructions.

- Optimize common operations, not the size of the instruction manual.
- Measure implementation cost as well as instruction count.
- Use fast hardwired control where possible.
- Let compilers combine simple operations into program behavior.
- Spend available chip area on resources that improve common cases.

**Speaker notes**

The paper’s importance is not the slogan “fewer instructions.” It proposes a different optimization target. The relevant outcome is program performance at an acceptable implementation cost. A reduced instruction set is useful when simpler decoding and control allow common instructions to execute predictably and when compiler-generated sequences replace rarely used complex features without losing the implementation advantage.

Source: [Patterson & Ditzel, 1980](https://dl.acm.org/doi/10.1145/641914.641917).

---

## Slide 4 — The 1980 argument, step by step

**On-slide text**

1. Measurements show that programs repeatedly use a relatively small set of operations.
2. Complex instructions require extra decoding, control, design effort, and verification.
3. Those costs can affect common instructions even when the complex operations are rare.
4. Simple encodings and control make short, regular execution paths more feasible.
5. Compiler-generated sequences can express the less common work.

**Design consequence:** instruction count alone is an incomplete performance metric.

**Speaker notes**

The key trade-off is explicit. A RISC program may execute more instructions, but each instruction can be simpler and more regular. This opens opportunities for faster control and, in later RISC designs, effective pipelining. The right comparison therefore includes cycle time and cycles per instruction, not just code length. For our project, that means we record cycle count and CPI and do not claim success only because the MoMo routine is short.

Source: [Patterson & Ditzel, 1980](https://dl.acm.org/doi/10.1145/641914.641917).

---

## Slide 5 — Critical reading of “The Case for RISC”

**On-slide text**

**Strong contribution**

- Reframes architecture as a hardware–compiler co-design problem.
- Challenges feature growth with workload and implementation evidence.
- Makes simplicity an engineering resource, not merely an aesthetic choice.

**Limits and open questions**

- More instructions can increase code size and instruction-memory traffic.
- Compiler quality becomes more important.
- Workload observations may not transfer unchanged to every application.
- The 1980 paper argues a direction; a working implementation still has to prove feasibility.

**Speaker notes**

We read the paper as a strong design case, not a universal rule that the smallest instruction set always wins. Removing an operation is beneficial only if the replacement sequences and memory-system effects remain acceptable. This is why the follow-up RISC I paper matters: it tests whether the proposed simplicity can be organized into a real processor.

Source: [Patterson & Ditzel, 1980](https://dl.acm.org/doi/10.1145/641914.641917).

---

## Slide 6 — Patterson & Séquin (1981): RISC I as the experiment

**On-slide text**

RISC I turns the earlier argument into a single-chip VLSI design.

- A small, regular instruction repertoire
- Fixed-size instruction words and simple decode
- Register-to-register arithmetic
- Explicit load/store access to memory
- Hardware support aimed at common high-level-language behavior

**Research question:** can a reduced architecture remain useful for compiled programs while being simpler to implement?

**Speaker notes**

RISC I is the concrete architectural response to the 1980 critique. It keeps arithmetic operations on registers and makes memory movement explicit. Regularity is important because it reduces the number of exceptional paths in the datapath and control. The paper also considers procedure calls, a frequent high-level-language operation, showing that “reduced” does not mean ignoring workload behavior.

Source: [Patterson & Séquin, 1981](https://people.eecs.berkeley.edu/~sequin/X/CCD_RISC_VLSI/RISC1_Patterson_Sequin_1981.pdf).

---

## Slide 7 — RISC I’s architectural choices

**On-slide text**

| Choice | Why it supports the RISC goal |
|---|---|
| Uniform instruction size | Predictable fetch and simpler field extraction |
| Few instruction formats | Less decode and control variation |
| Register-register ALU operations | Regular datapath inputs and outputs |
| Load/store memory model | Memory behavior is explicit and isolated |
| Simple addressing | Effective address can be formed by ordinary arithmetic hardware |

**Speaker notes**

These choices reinforce one another. Uniform words make the next instruction boundary obvious. A small number of field layouts lets hardware select register addresses without many format-specific cases. Load/store organization means arithmetic instructions do not also need a memory access path. Together, these choices make a regular implementation possible; no single row provides the whole advantage by itself.

Source: [Patterson & Séquin, 1981](https://people.eecs.berkeley.edu/~sequin/X/CCD_RISC_VLSI/RISC1_Patterson_Sequin_1981.pdf).

---

## Slide 8 — Procedure calls and register windows

**On-slide text**

RISC I uses overlapping register windows to reduce the cost of procedure calls.

- A procedure sees a working set of registers.
- Adjacent windows overlap so arguments can be passed without ordinary memory traffic.
- A call changes the active window instead of saving every register immediately.
- Infrequent overflow/underflow cases are handled separately.

**Lesson:** RISC removes general complexity but may retain targeted hardware for a demonstrably frequent case.

**Speaker notes**

Register windows prevent a simplistic reading of RISC. The design includes specialized support when the authors believe the workload justifies it. The support is structured and localized: common calls can be cheap without making every arithmetic instruction more complicated. GhanaCore-5 does not implement windows because our 18-instruction transaction routine and course scope do not need procedures, but the reasoning method still applies.

Source: [Patterson & Séquin, 1981](https://people.eecs.berkeley.edu/~sequin/X/CCD_RISC_VLSI/RISC1_Patterson_Sequin_1981.pdf).

---

## Slide 9 — What RISC I demonstrates, and what it does not settle

**On-slide text**

**Demonstrates**

- A reduced, regular architecture can be implemented as a practical VLSI design.
- Simple instruction behavior and high-level-language support can coexist.
- Architecture, compiler assumptions, and chip organization should be evaluated together.

**Does not settle**

- One prototype cannot represent every future workload or fabrication process.
- Code density and memory-system effects remain real trade-offs.
- Results depend on the compiler, benchmark selection, and comparison baseline.

**Speaker notes**

The paper supplies evidence of feasibility, not a timeless numerical guarantee. Its lasting value is the disciplined organization of the processor around common operations and regular control. Modern systems may make different trade-offs, but we can still test the same questions in GhanaCore-5: Is the encoding unambiguous? Are control signals deterministic? Can software and hardware models agree cycle by cycle?

Source: [Patterson & Séquin, 1981](https://people.eecs.berkeley.edu/~sequin/X/CCD_RISC_VLSI/RISC1_Patterson_Sequin_1981.pdf).

---

## Slide 10 — How the two papers fit together

**On-slide text**

| 1980: “Case for RISC” | 1981: “RISC I” |
|---|---|
| Diagnoses the cost of instruction-set complexity | Builds a processor around the proposed alternative |
| Argues from instruction use and implementation cost | Defines concrete encodings, registers, and datapath behavior |
| Treats compiler support as part of the solution | Organizes hardware for compiled high-level-language programs |
| Proposes simplicity as a performance enabler | Tests simplicity in a VLSI implementation |

**Combined conclusion:** reduction is valuable when it creates measurable regularity in the whole hardware–software system.

**Speaker notes**

The papers should not be presented as two disconnected summaries. The first changes the design objective; the second evaluates that objective in a real architecture. This sequence also describes our project workflow: define a small ISA, encode it precisely, implement hardware and software models, and compare observable state rather than relying on a verbal claim of correctness.

Sources: [Patterson & Ditzel, 1980](https://dl.acm.org/doi/10.1145/641914.641917); [Patterson & Séquin, 1981](https://people.eecs.berkeley.edu/~sequin/X/CCD_RISC_VLSI/RISC1_Patterson_Sequin_1981.pdf).

---

## Slide 11 — Explicit connection to GhanaCore-5

**On-slide text**

| RISC argument | GhanaCore-5 design decision |
|---|---|
| Regular instruction representation | Every instruction is exactly 32 bits |
| Simple field extraction | 6-bit opcode and fixed 4-bit register positions |
| Load/store separation | Only `LW` and `SW` access data memory |
| Small operation set | 12 opcodes cover arithmetic, logic, immediate, branch, memory, and NOP |
| Predictable datapath work | IF → ID → EX → MEM → WB stages |
| Compiler/software responsibility | Two-pass assembler resolves labels; NOPs handle baseline data hazards |
| Verify the whole system | Logisim state is compared with the golden C cycle trace |

**Closing statement:** our five-stage design is not a copy of RISC I; it is a course-scale application of the papers’ central principle—regularity must be made concrete in the encoding, control, datapath, and software tools.

**Speaker notes**

Our 32-bit word has the opcode in bits 31 to 26, fixed register fields, and an 18-bit signed immediate. The control unit maps each legal opcode to one control word. Pipeline boundaries carry only named data and control fields. The MoMo routine exercises the design with a bounds check, a balance check, a load, a store, arithmetic, and explicit branches. The strongest connection to the papers is therefore testable regularity: the assembler, simulator, truth table, and Logisim circuit all use the same encoding.

Project artifacts: `isa/isa.h`, `isa/isa.py`, `docs/opcode_and_instruction_formats.md`, `docs/control_truth_table.md`, and `docs/pipeline_register_spec.md`.

---

## References slide (optional if a 12th slide is allowed)

- Patterson, D. A., & Ditzel, D. R. (1980). “The Case for the Reduced Instruction Set Computer.” *ACM SIGARCH Computer Architecture News*, 8(6). [ACM DOI record](https://dl.acm.org/doi/10.1145/641914.641917).
- Patterson, D. A., & Séquin, C. H. (1981). “RISC I: A Reduced Instruction Set VLSI Computer.” *Proceedings of the 8th Annual Symposium on Computer Architecture*. [Author-hosted paper](https://people.eecs.berkeley.edu/~sequin/X/CCD_RISC_VLSI/RISC1_Patterson_Sequin_1981.pdf).
