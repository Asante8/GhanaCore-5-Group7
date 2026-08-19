#include <errno.h>
#include <inttypes.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "control_unit.h"
#include "isa.h"
#include "register_file.h"

#define IMEM_CAPACITY 1024u
#define DMEM_WORDS 256u
#define TRACE_MEMORY_WORDS 16u
#define DEFAULT_MAX_CYCLES 10000u

typedef struct {
    bool valid;
    uint32_t pc;
    uint32_t instruction;
} IfIdRegister;

typedef struct {
    bool valid;
    uint32_t pc;
    GhanaDecoded decoded;
    int32_t rs1_value;
    int32_t rs2_value;
    int32_t immediate;
    GhanaControl control;
} IdExRegister;

typedef struct {
    bool valid;
    uint32_t pc;
    GhanaOpcode opcode;
    int32_t alu_result;
    int32_t store_data;
    uint8_t destination;
    bool branch_taken;
    uint32_t branch_target;
    GhanaControl control;
} ExMemRegister;

typedef struct {
    bool valid;
    GhanaOpcode opcode;
    int32_t memory_data;
    int32_t alu_result;
    uint8_t destination;
    bool reg_write;
    bool mem_to_reg;
} MemWbRegister;

typedef struct {
    uint32_t instruction_memory[IMEM_CAPACITY];
    size_t instruction_count;
    int32_t data_memory[DMEM_WORDS];
    GhanaRegisterFile register_file;
    uint32_t pc;
    uint64_t cycle;
    uint64_t retired;
    IfIdRegister if_id;
    IdExRegister id_ex;
    ExMemRegister ex_mem;
    MemWbRegister mem_wb;
} Simulator;

typedef struct {
    const char *instruction_path;
    const char *data_path;
    const char *trace_path;
    uint64_t max_cycles;
    bool quiet;
} Options;

static void usage(const char *program) {
    fprintf(
        stderr,
        "Usage: %s PROGRAM.hex [--data DATA.hex] [--trace TRACE.csv] [--max-cycles N] [--quiet]\n",
        program
    );
}

static bool parse_u64(const char *text, uint64_t *value) {
    char *end = NULL;
    errno = 0;
    unsigned long long parsed = strtoull(text, &end, 0);
    if (errno != 0 || end == text || *end != '\0') {
        return false;
    }
    *value = (uint64_t)parsed;
    return true;
}

static bool parse_options(int argc, char **argv, Options *options) {
    if (argc < 2) {
        return false;
    }
    *options = (Options){
        .instruction_path = argv[1],
        .data_path = NULL,
        .trace_path = "trace.csv",
        .max_cycles = DEFAULT_MAX_CYCLES,
        .quiet = false,
    };
    for (int index = 2; index < argc; ++index) {
        if (strcmp(argv[index], "--data") == 0 && index + 1 < argc) {
            options->data_path = argv[++index];
        } else if (strcmp(argv[index], "--trace") == 0 && index + 1 < argc) {
            options->trace_path = argv[++index];
        } else if (strcmp(argv[index], "--max-cycles") == 0 && index + 1 < argc) {
            if (!parse_u64(argv[++index], &options->max_cycles) || options->max_cycles == 0u) {
                fprintf(stderr, "invalid --max-cycles value\n");
                return false;
            }
        } else if (strcmp(argv[index], "--quiet") == 0) {
            options->quiet = true;
        } else {
            fprintf(stderr, "unknown or incomplete option: %s\n", argv[index]);
            return false;
        }
    }
    return true;
}

static void trim_comment(char *line) {
    char *hash = strchr(line, '#');
    char *semicolon = strchr(line, ';');
    char *cut = NULL;
    if (hash != NULL && semicolon != NULL) {
        cut = hash < semicolon ? hash : semicolon;
    } else if (hash != NULL) {
        cut = hash;
    } else if (semicolon != NULL) {
        cut = semicolon;
    }
    if (cut != NULL) {
        *cut = '\0';
    }
}

static bool parse_hex_word(const char *line, uint32_t *word) {
    while (*line == ' ' || *line == '\t' || *line == '\r' || *line == '\n') {
        ++line;
    }
    if (*line == '\0') {
        return false;
    }
    char *end = NULL;
    errno = 0;
    unsigned long parsed = strtoul(line, &end, 16);
    if (errno != 0 || end == line || parsed > UINT32_MAX) {
        return false;
    }
    while (*end == ' ' || *end == '\t' || *end == '\r' || *end == '\n') {
        ++end;
    }
    if (*end != '\0') {
        return false;
    }
    *word = (uint32_t)parsed;
    return true;
}

static bool load_instruction_memory(Simulator *simulator, const char *path) {
    FILE *file = fopen(path, "r");
    if (file == NULL) {
        perror(path);
        return false;
    }
    char line[256];
    size_t line_number = 0u;
    while (fgets(line, sizeof(line), file) != NULL) {
        ++line_number;
        trim_comment(line);
        const char *cursor = line;
        while (*cursor == ' ' || *cursor == '\t' || *cursor == '\r' || *cursor == '\n') {
            ++cursor;
        }
        if (*cursor == '\0') {
            continue;
        }
        uint32_t word = 0u;
        if (!parse_hex_word(cursor, &word)) {
            fprintf(stderr, "%s:%zu: invalid 32-bit hexadecimal instruction\n", path, line_number);
            fclose(file);
            return false;
        }
        if (simulator->instruction_count >= IMEM_CAPACITY) {
            fprintf(stderr, "%s: instruction memory capacity exceeded\n", path);
            fclose(file);
            return false;
        }
        simulator->instruction_memory[simulator->instruction_count++] = word;
    }
    if (ferror(file)) {
        perror(path);
        fclose(file);
        return false;
    }
    fclose(file);
    return true;
}

static bool load_data_memory(Simulator *simulator, const char *path) {
    if (path == NULL) {
        return true;
    }
    FILE *file = fopen(path, "r");
    if (file == NULL) {
        perror(path);
        return false;
    }
    char line[256];
    size_t address = 0u;
    size_t line_number = 0u;
    while (fgets(line, sizeof(line), file) != NULL) {
        ++line_number;
        trim_comment(line);
        const char *cursor = line;
        while (*cursor == ' ' || *cursor == '\t' || *cursor == '\r' || *cursor == '\n') {
            ++cursor;
        }
        if (*cursor == '\0') {
            continue;
        }
        uint32_t word = 0u;
        if (!parse_hex_word(cursor, &word)) {
            fprintf(stderr, "%s:%zu: invalid 32-bit hexadecimal data word\n", path, line_number);
            fclose(file);
            return false;
        }
        if (address >= DMEM_WORDS) {
            fprintf(stderr, "%s: data memory capacity exceeded\n", path);
            fclose(file);
            return false;
        }
        simulator->data_memory[address++] = (int32_t)word;
    }
    if (ferror(file)) {
        perror(path);
        fclose(file);
        return false;
    }
    fclose(file);
    return true;
}

static int32_t execute_alu(GhanaAluOp operation, int32_t left, int32_t right) {
    switch (operation) {
        case ALU_ADD:
            return (int32_t)((uint32_t)left + (uint32_t)right);
        case ALU_SUB:
            return (int32_t)((uint32_t)left - (uint32_t)right);
        case ALU_AND:
            return left & right;
        case ALU_OR:
            return left | right;
        case ALU_XOR:
            return left ^ right;
        case ALU_SLT:
            return left < right ? 1 : 0;
        case ALU_PASS:
        default:
            return 0;
    }
}

static bool pipeline_empty(const Simulator *simulator) {
    return !simulator->if_id.valid && !simulator->id_ex.valid && !simulator->ex_mem.valid && !simulator->mem_wb.valid;
}

static void write_trace_header(FILE *trace) {
    fprintf(trace, "cycle,pc_next,if_valid,if_pc,if_instruction,if_opcode,id_opcode,ex_opcode,mem_opcode");
    for (unsigned register_index = 0u; register_index < GHANACORE_REGISTER_COUNT; ++register_index) {
        fprintf(trace, ",r%u", register_index);
    }
    for (unsigned address = 0u; address < TRACE_MEMORY_WORDS; ++address) {
        fprintf(trace, ",m%u", address);
    }
    fputc('\n', trace);
}

static unsigned opcode_or_bubble(bool valid, GhanaOpcode opcode) {
    return valid ? (unsigned)opcode : 0xFFu;
}

static void write_trace_row(FILE *trace, const Simulator *simulator) {
    unsigned if_opcode = simulator->if_id.valid
        ? (simulator->if_id.instruction >> GHANACORE_OPCODE_SHIFT) & GHANACORE_OPCODE_MASK
        : 0xFFu;
    fprintf(
        trace,
        "%" PRIu64 ",%" PRIu32 ",%u,%" PRIu32 ",%08" PRIX32 ",%u,%u,%u,%u",
        simulator->cycle,
        simulator->pc,
        simulator->if_id.valid ? 1u : 0u,
        simulator->if_id.pc,
        simulator->if_id.instruction,
        if_opcode,
        opcode_or_bubble(simulator->id_ex.valid, simulator->id_ex.decoded.opcode),
        opcode_or_bubble(simulator->ex_mem.valid, simulator->ex_mem.opcode),
        opcode_or_bubble(simulator->mem_wb.valid, simulator->mem_wb.opcode)
    );
    for (unsigned register_index = 0u; register_index < GHANACORE_REGISTER_COUNT; ++register_index) {
        fprintf(trace, ",%" PRId32, ghana_rf_read(&simulator->register_file, (uint8_t)register_index));
    }
    for (unsigned address = 0u; address < TRACE_MEMORY_WORDS; ++address) {
        fprintf(trace, ",%" PRId32, simulator->data_memory[address]);
    }
    fputc('\n', trace);
}

static bool run_cycle(Simulator *simulator, FILE *trace) {
    IfIdRegister next_if_id = {0};
    IdExRegister next_id_ex = {0};
    ExMemRegister next_ex_mem = {0};
    MemWbRegister next_mem_wb = {0};

    ++simulator->cycle;

    /* WB happens first so ID can observe a same-cycle write. */
    if (simulator->mem_wb.valid) {
        int32_t write_data = simulator->mem_wb.mem_to_reg
            ? simulator->mem_wb.memory_data
            : simulator->mem_wb.alu_result;
        ghana_rf_write(
            &simulator->register_file,
            simulator->mem_wb.destination,
            write_data,
            simulator->mem_wb.reg_write
        );
        ++simulator->retired;
    }

    /* MEM */
    if (simulator->ex_mem.valid) {
        next_mem_wb.valid = true;
        next_mem_wb.opcode = simulator->ex_mem.opcode;
        next_mem_wb.alu_result = simulator->ex_mem.alu_result;
        next_mem_wb.destination = simulator->ex_mem.destination;
        next_mem_wb.reg_write = simulator->ex_mem.control.reg_write;
        next_mem_wb.mem_to_reg = simulator->ex_mem.control.mem_to_reg;

        if (simulator->ex_mem.control.mem_read || simulator->ex_mem.control.mem_write) {
            int32_t address = simulator->ex_mem.alu_result;
            if (address < 0 || (uint32_t)address >= DMEM_WORDS) {
                fprintf(stderr, "cycle %" PRIu64 ": data-memory address %" PRId32 " is out of range\n", simulator->cycle, address);
                return false;
            }
            if (simulator->ex_mem.control.mem_read) {
                next_mem_wb.memory_data = simulator->data_memory[(uint32_t)address];
            }
            if (simulator->ex_mem.control.mem_write) {
                simulator->data_memory[(uint32_t)address] = simulator->ex_mem.store_data;
            }
        }
    }

    /* EX */
    if (simulator->id_ex.valid) {
        int32_t right = simulator->id_ex.control.alu_src_imm
            ? simulator->id_ex.immediate
            : simulator->id_ex.rs2_value;
        next_ex_mem.valid = true;
        next_ex_mem.pc = simulator->id_ex.pc;
        next_ex_mem.opcode = simulator->id_ex.decoded.opcode;
        next_ex_mem.alu_result = execute_alu(simulator->id_ex.control.alu_op, simulator->id_ex.rs1_value, right);
        next_ex_mem.store_data = simulator->id_ex.rs2_value;
        next_ex_mem.destination = simulator->id_ex.decoded.rd;
        next_ex_mem.control = simulator->id_ex.control;

        if (simulator->id_ex.control.branch) {
            bool equal = simulator->id_ex.rs1_value == simulator->id_ex.rs2_value;
            next_ex_mem.branch_taken = simulator->id_ex.control.branch_not_equal ? !equal : equal;
            int64_t target = (int64_t)simulator->id_ex.pc + 1 + simulator->id_ex.immediate;
            if (target < 0 || target > UINT32_MAX) {
                fprintf(stderr, "cycle %" PRIu64 ": branch target is out of range\n", simulator->cycle);
                return false;
            }
            next_ex_mem.branch_target = (uint32_t)target;
        }
    }

    /* ID */
    if (simulator->if_id.valid) {
        GhanaDecoded decoded = ghana_decode(simulator->if_id.instruction);
        GhanaControl control = ghana_control_for_opcode((uint8_t)decoded.opcode);
        if (!control.valid) {
            fprintf(
                stderr,
                "cycle %" PRIu64 ": unsupported opcode 0x%02X at PC %" PRIu32 "\n",
                simulator->cycle,
                (unsigned)decoded.opcode,
                simulator->if_id.pc
            );
            return false;
        }
        next_id_ex.valid = true;
        next_id_ex.pc = simulator->if_id.pc;
        next_id_ex.decoded = decoded;
        next_id_ex.immediate = decoded.immediate;
        next_id_ex.control = control;
        ghana_rf_read2(
            &simulator->register_file,
            decoded.rs1,
            decoded.rs2,
            &next_id_ex.rs1_value,
            &next_id_ex.rs2_value
        );
    }

    /* IF */
    if (simulator->pc < simulator->instruction_count) {
        next_if_id.valid = true;
        next_if_id.pc = simulator->pc;
        next_if_id.instruction = simulator->instruction_memory[simulator->pc];
        ++simulator->pc;
    }

    /* A taken EX-stage branch discards the two younger instructions. */
    if (next_ex_mem.valid && next_ex_mem.branch_taken) {
        next_id_ex.valid = false;
        next_if_id.valid = false;
        simulator->pc = next_ex_mem.branch_target;
    }

    simulator->if_id = next_if_id;
    simulator->id_ex = next_id_ex;
    simulator->ex_mem = next_ex_mem;
    simulator->mem_wb = next_mem_wb;
    write_trace_row(trace, simulator);
    return true;
}

static void print_final_state(const Simulator *simulator, const char *trace_path) {
    double cpi = simulator->retired == 0u ? 0.0 : (double)simulator->cycle / (double)simulator->retired;
    printf(
        "Simulation complete: cycles=%" PRIu64 ", retired=%" PRIu64 ", CPI=%.3f, trace=%s\n",
        simulator->cycle,
        simulator->retired,
        cpi,
        trace_path
    );
    for (unsigned index = 0u; index < GHANACORE_REGISTER_COUNT; ++index) {
        printf(
            "r%-2u=%" PRId32 "%c",
            index,
            ghana_rf_read(&simulator->register_file, (uint8_t)index),
            index % 4u == 3u ? '\n' : '\t'
        );
    }
    printf(
        "memory[0..3]=[%" PRId32 ", %" PRId32 ", %" PRId32 ", %" PRId32 "]\n",
        simulator->data_memory[0],
        simulator->data_memory[1],
        simulator->data_memory[2],
        simulator->data_memory[3]
    );
}

int main(int argc, char **argv) {
    Options options;
    if (!parse_options(argc, argv, &options)) {
        usage(argv[0]);
        return EXIT_FAILURE;
    }

    Simulator simulator = {0};
    ghana_rf_reset(&simulator.register_file);
    if (!load_instruction_memory(&simulator, options.instruction_path)) {
        return EXIT_FAILURE;
    }
    if (!load_data_memory(&simulator, options.data_path)) {
        return EXIT_FAILURE;
    }

    FILE *trace = fopen(options.trace_path, "w");
    if (trace == NULL) {
        perror(options.trace_path);
        return EXIT_FAILURE;
    }
    write_trace_header(trace);

    bool success = true;
    while ((simulator.pc < simulator.instruction_count || !pipeline_empty(&simulator)) && simulator.cycle < options.max_cycles) {
        if (!run_cycle(&simulator, trace)) {
            success = false;
            break;
        }
    }
    if (simulator.cycle >= options.max_cycles && (simulator.pc < simulator.instruction_count || !pipeline_empty(&simulator))) {
        fprintf(stderr, "simulation exceeded maximum cycle count %" PRIu64 "\n", options.max_cycles);
        success = false;
    }
    if (fclose(trace) != 0) {
        perror(options.trace_path);
        success = false;
    }
    if (success && !options.quiet) {
        print_final_state(&simulator, options.trace_path);
    }
    return success ? EXIT_SUCCESS : EXIT_FAILURE;
}
