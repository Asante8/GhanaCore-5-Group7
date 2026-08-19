# Hazard-safe baseline for a five-stage pipeline with no forwarding/interlocks.
# The implementation writes WB before ID reads in the same cycle.

        LW    r1, 0(r0)
        LW    r2, 1(r0)
        LW    r3, 2(r0)
        LW    r4, 3(r0)
        NOP
        ADD   r5, r2, r3
        SLT   r6, r4, r2
        NOP
        NOP
        BNE   r6, r0, reject
        NOP
        NOP
        SLT   r7, r1, r5
        NOP
        NOP
        BNE   r7, r0, reject
        NOP
        NOP
        SUB   r1, r1, r5
        NOP
        NOP
        SW    r1, 0(r0)
        ADDI  r8, r0, 1
        OR    r9, r2, r3
        XOR   r10, r2, r3
        AND   r11, r2, r3
        BEQ   r0, r0, done
        NOP
        NOP
reject:
        ADDI  r8, r0, 0
done:
        NOP
