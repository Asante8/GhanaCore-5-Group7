#ifndef GHANACORE_CONTROL_UNIT_H
#define GHANACORE_CONTROL_UNIT_H

#include <stdbool.h>
#include <stdint.h>

#include "isa.h"

typedef enum {
    ALU_ADD = 0,
    ALU_SUB = 1,
    ALU_AND = 2,
    ALU_OR = 3,
    ALU_XOR = 4,
    ALU_SLT = 5,
    ALU_PASS = 6
} GhanaAluOp;

typedef struct {
    bool valid;
    bool reg_write;
    bool mem_read;
    bool mem_write;
    bool mem_to_reg;
    bool alu_src_imm;
    bool branch;
    bool branch_not_equal;
    GhanaAluOp alu_op;
} GhanaControl;

static inline GhanaControl ghana_control_for_opcode(uint8_t opcode) {
    GhanaControl control = {
        .valid = true,
        .reg_write = false,
        .mem_read = false,
        .mem_write = false,
        .mem_to_reg = false,
        .alu_src_imm = false,
        .branch = false,
        .branch_not_equal = false,
        .alu_op = ALU_PASS,
    };

    switch ((GhanaOpcode)opcode) {
        case OP_NOP:
            break;
        case OP_ADD:
            control.reg_write = true;
            control.alu_op = ALU_ADD;
            break;
        case OP_SUB:
            control.reg_write = true;
            control.alu_op = ALU_SUB;
            break;
        case OP_AND:
            control.reg_write = true;
            control.alu_op = ALU_AND;
            break;
        case OP_OR:
            control.reg_write = true;
            control.alu_op = ALU_OR;
            break;
        case OP_XOR:
            control.reg_write = true;
            control.alu_op = ALU_XOR;
            break;
        case OP_SLT:
            control.reg_write = true;
            control.alu_op = ALU_SLT;
            break;
        case OP_ADDI:
            control.reg_write = true;
            control.alu_src_imm = true;
            control.alu_op = ALU_ADD;
            break;
        case OP_LW:
            control.reg_write = true;
            control.mem_read = true;
            control.mem_to_reg = true;
            control.alu_src_imm = true;
            control.alu_op = ALU_ADD;
            break;
        case OP_SW:
            control.mem_write = true;
            control.alu_src_imm = true;
            control.alu_op = ALU_ADD;
            break;
        case OP_BEQ:
            control.branch = true;
            control.alu_op = ALU_SUB;
            break;
        case OP_BNE:
            control.branch = true;
            control.branch_not_equal = true;
            control.alu_op = ALU_SUB;
            break;
        default:
            control.valid = false;
            break;
    }
    return control;
}

#endif
