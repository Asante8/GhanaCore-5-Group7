# Testing, verification, or review conducted

Group 7, University of Ghana — verified on 19 August 2026.

## Reproducible command

```sh
make test
```

The implementation uses only a C11 compiler and Python 3.10 or newer. The test run completed with compiler flags `-Wall -Wextra -Wpedantic -Werror`, so warnings are treated as build failures.

## Recorded results

```text
[PASS] RegisterFile16x32: dual-read, single-write, write-enable, and r0 behavior
[PASS] ControlUnit: all 12 legal opcodes and one reserved opcode
[PASS] Decoder: fixed fields and signed immediate
ALL C CORE TESTS PASSED (18 checks)

Ran 8 tests
OK
```

The eight Python tests cover:

1. Exact comparison of all 18 generated machine words with independently hand-computed hexadecimal values.
2. Forward- and backward-label resolution by the two-pass assembler.
3. Presence of arithmetic, immediate, branch, load, store, and NOP classes in the routine.
4. Rejection of an invalid register number.
5. Per-opcode comparison of all control signals against an independent expected-value table.
6. Rejection of a reserved opcode.
7. Accepted-transaction pipeline integration.
8. Rejected-transaction pipeline integration.

## Golden-simulator integration results

| Scenario | Cycles | Retired instructions | CPI | Final balance `memory[0]` | `r8` | Result |
|---|---:|---:|---:|---:|---:|---|
| Accepted: balance 1000, amount 150, fee 10, limit 500 | 34 | 28 | 1.214 | 840 | 1 | PASS |
| Rejected: balance 1000, amount 600, fee 10, limit 500 | 18 | 12 | 1.500 | 1000 | 0 | PASS |

For the accepted case, the additional logic-check registers finished as `r9=158` (`150 OR 10`), `r10=156` (`150 XOR 10`), and `r11=2` (`150 AND 10`). For the rejected case, the first bounds-check branch was taken and the balance remained unchanged.

The accepted run produced `build/momo_trace.csv`; the rejected run produced `build/momo_reject_trace.csv`. Each trace records every cycle’s next PC, IF instruction, IF/ID/EX/MEM opcode occupancy, all sixteen registers, and data-memory words 0–15. Bubble opcodes appear as decimal `255`. These columns are the software-side comparison points for Logisim probes.

## Report-ready summary

The register file was unit-tested for simultaneous dual reads, a single enabled write, disabled-write preservation, and hardwired-zero behavior. The control unit was checked for every legal opcode and an illegal opcode against hand-computed values. The two-pass assembler reproduced all 18 expected instruction words and resolved both forward and backward labels. End-to-end simulation of the NOP-padded program passed both acceptance and rejection cases, exporting per-cycle register and memory state to CSV. No mismatches remained after verification.
