# GhanaCore-5 Group 7 MoMo debit routine — 18 instructions.
# Word-addressed data memory:
#   memory[0] = balance, memory[1] = amount,
#   memory[2] = fee,     memory[3] = transaction limit.
# Result: r8=1 and updated memory[0] when accepted; r8=0 when rejected.

        LW    r1, 0(r0)          # balance
        LW    r2, 1(r0)          # amount
        LW    r3, 2(r0)          # fee
        LW    r4, 3(r0)          # per-transaction limit
        ADD   r5, r2, r3         # total debit = amount + fee
        SLT   r6, r4, r2         # amount > limit?
        BNE   r6, r0, reject     # bounds-check branch
        SLT   r7, r1, r5         # balance < total debit?
        BNE   r7, r0, reject
        SUB   r1, r1, r5         # balance -= total debit
        SW    r1, 0(r0)          # store new balance
        ADDI  r8, r0, 1          # accepted = 1
        OR    r9, r2, r3         # arithmetic/logic self-check values
        XOR   r10, r2, r3
        AND   r11, r2, r3
        BEQ   r0, r0, done       # skip rejection path
reject:
        ADDI  r8, r0, 0          # accepted = 0
done:
        NOP
