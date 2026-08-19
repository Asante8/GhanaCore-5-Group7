#ifndef GHANACORE_REGISTER_FILE_H
#define GHANACORE_REGISTER_FILE_H

#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#include "isa.h"

typedef struct {
    int32_t registers[GHANACORE_REGISTER_COUNT];
} GhanaRegisterFile;

static inline void ghana_rf_reset(GhanaRegisterFile *file) {
    memset(file->registers, 0, sizeof(file->registers));
}

static inline int32_t ghana_rf_read(const GhanaRegisterFile *file, uint8_t address) {
    address &= GHANACORE_REGISTER_MASK;
    return address == 0u ? 0 : file->registers[address];
}

static inline void ghana_rf_read2(
    const GhanaRegisterFile *file,
    uint8_t read_address_1,
    uint8_t read_address_2,
    int32_t *read_data_1,
    int32_t *read_data_2
) {
    *read_data_1 = ghana_rf_read(file, read_address_1);
    *read_data_2 = ghana_rf_read(file, read_address_2);
}

static inline void ghana_rf_write(
    GhanaRegisterFile *file,
    uint8_t write_address,
    int32_t write_data,
    bool write_enable
) {
    write_address &= GHANACORE_REGISTER_MASK;
    if (write_enable && write_address != 0u) {
        file->registers[write_address] = write_data;
    }
    file->registers[0] = 0;
}

#endif
