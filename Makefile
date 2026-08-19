PYTHON ?= python3
CC ?= cc
CFLAGS ?= -std=c11 -Wall -Wextra -Wpedantic -Werror -O2

BUILD_DIR := build
SIMULATOR := $(BUILD_DIR)/simulator
CORE_TEST := $(BUILD_DIR)/test_core
ASSEMBLER := assembler/assembler.py

.PHONY: all assemble test run clean

all: $(SIMULATOR) assemble

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(SIMULATOR): simulator/simulator.c simulator/control_unit.h simulator/register_file.h isa/isa.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) -Iisa -Isimulator simulator/simulator.c -o $(SIMULATOR)

$(CORE_TEST): tests/test_core.c simulator/control_unit.h simulator/register_file.h isa/isa.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) -Iisa -Isimulator tests/test_core.c -o $(CORE_TEST)

assemble:
	$(PYTHON) $(ASSEMBLER) programs/momo_routine.s -o programs/momo_routine.hex --listing programs/momo_routine.lst --csv programs/momo_routine.csv --markdown docs/momo_routine_machine_code.md
	$(PYTHON) $(ASSEMBLER) programs/momo_routine_nop_padded.s -o programs/momo_routine_nop_padded.hex --listing programs/momo_routine_nop_padded.lst --csv programs/momo_routine_nop_padded.csv

test: all $(CORE_TEST)
	./$(CORE_TEST)
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py' -v

run: all
	./$(SIMULATOR) programs/momo_routine_nop_padded.hex --data programs/data_memory.hex --trace $(BUILD_DIR)/momo_trace.csv

clean:
	rm -rf $(BUILD_DIR) programs/*.hex programs/*.lst programs/*.csv docs/momo_routine_machine_code.md

