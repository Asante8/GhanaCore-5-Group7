#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#include "control_unit.h"
#include "isa.h"
#include "register_file.h"

typedef struct {
    GhanaOpcode opcode;
    bool reg_write;
    bool mem_read;
    bool mem_write;
    bool mem_to_reg;
    bool alu_src_imm;
    bool branch;
    bool branch_not_equal;
    GhanaAluOp alu_op;
} ExpectedControl;

static int checks = 0;
static int failures = 0;

static void expect_true(bool condition, const char *message) {
    ++checks;
    if (!condition) {
        ++failures;
        fprintf(stderr, "[FAIL] %s\n", message);
    }
}

static void test_register_file(void) {
    GhanaRegisterFile file;
    ghana_rf_reset(&file);

    ghana_rf_write(&file, 3u, 1234, true);
    ghana_rf_write(&file, 9u, -77, true);
    int32_t port_a = 0;
    int32_t port_b = 0;
    ghana_rf_read2(&file, 3u, 9u, &port_a, &port_b);
    expect_true(port_a == 1234 && port_b == -77, "dual read returns both independently written values");

    ghana_rf_write(&file, 3u, 9999, false);
    expect_true(ghana_rf_read(&file, 3u) == 1234, "write-enable zero preserves register contents");

    ghana_rf_write(&file, 0u, 55, true);
    expect_true(ghana_rf_read(&file, 0u) == 0, "r0 remains hardwired to zero after an enabled write");

    puts("[PASS] RegisterFile16x32: dual-read, single-write, write-enable, and r0 behavior");
}

static void test_control_unit(void) {
    static const ExpectedControl expected[] = {
        {OP_NOP,  false, false, false, false, false, false, false, ALU_PASS},
        {OP_ADD,  true,  false, false, false, false, false, false, ALU_ADD},
        {OP_SUB,  true,  false, false, false, false, false, false, ALU_SUB},
        {OP_AND,  true,  false, false, false, false, false, false, ALU_AND},
        {OP_OR,   true,  false, false, false, false, false, false, ALU_OR},
        {OP_XOR,  true,  false, false, false, false, false, false, ALU_XOR},
        {OP_SLT,  true,  false, false, false, false, false, false, ALU_SLT},
        {OP_ADDI, true,  false, false, false, true,  false, false, ALU_ADD},
        {OP_LW,   true,  true,  false, true,  true,  false, false, ALU_ADD},
        {OP_SW,   false, false, true,  false, true,  false, false, ALU_ADD},
        {OP_BEQ,  false, false, false, false, false, true,  false, ALU_SUB},
        {OP_BNE,  false, false, false, false, false, true,  true,  ALU_SUB},
    };

    for (size_t index = 0u; index < sizeof(expected) / sizeof(expected[0]); ++index) {
        GhanaControl actual = ghana_control_for_opcode((uint8_t)expected[index].opcode);
        bool matches = actual.valid
            && actual.reg_write == expected[index].reg_write
            && actual.mem_read == expected[index].mem_read
            && actual.mem_write == expected[index].mem_write
            && actual.mem_to_reg == expected[index].mem_to_reg
            && actual.alu_src_imm == expected[index].alu_src_imm
            && actual.branch == expected[index].branch
            && actual.branch_not_equal == expected[index].branch_not_equal
            && actual.alu_op == expected[index].alu_op;
        expect_true(matches, "opcode control signals match the hand-computed truth table");
    }

    GhanaControl reserved = ghana_control_for_opcode(0x3Fu);
    expect_true(!reserved.valid, "reserved opcode 0x3F asserts Valid=0");
    puts("[PASS] ControlUnit: all 12 legal opcodes and one reserved opcode");
}

static void test_decoder(void) {
    GhanaDecoded lw = ghana_decode(0x40BFFFFFu); /* LW r2, -1(r15). */
    expect_true(lw.opcode == OP_LW && lw.rd == 2u && lw.rs1 == 15u && lw.immediate == -1,
                "I-format decoder extracts rd/base and sign-extends imm18");

    GhanaDecoded bne = ghana_decode(0x64180009u); /* BNE r6, r0, +9. */
    expect_true(bne.opcode == OP_BNE && bne.rs1 == 6u && bne.rs2 == 0u && bne.immediate == 9,
                "B-format decoder extracts both sources and PC-relative offset");
    puts("[PASS] Decoder: fixed fields and signed immediate");
}

int main(void) {
    test_register_file();
    test_control_unit();
    test_decoder();
    if (failures != 0) {
        fprintf(stderr, "%d of %d checks failed\n", failures, checks);
        return EXIT_FAILURE;
    }
    printf("ALL C CORE TESTS PASSED (%d checks)\n", checks);
    return EXIT_SUCCESS;
}
