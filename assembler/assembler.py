#!/usr/bin/env python3
"""Two-pass assembler for the GhanaCore-5 32-bit ISA."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from isa.isa import I_OPS, MNEMONIC_TO_OPCODE, R_OPS, Opcode, encode_i, encode_nop, encode_r, encode_sb


class AssemblerError(ValueError):
    """Source error with a useful line-number message."""


@dataclass(frozen=True)
class SourceInstruction:
    pc: int
    line_number: int
    text: str


@dataclass(frozen=True)
class AssembledInstruction:
    pc: int
    line_number: int
    source: str
    word: int


LABEL_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
REGISTER_RE = re.compile(r"^[Rr](\d+)$")
MEMORY_RE = re.compile(r"^(.+)\(([Rr]\d+)\)$")


def strip_comment(line: str) -> str:
    comment_positions = [position for token in ("#", ";") if (position := line.find(token)) >= 0]
    if comment_positions:
        line = line[: min(comment_positions)]
    return line.strip()


def parse_integer(token: str) -> int:
    try:
        return int(token.strip(), 0)
    except ValueError as exc:
        raise AssemblerError(f"invalid integer '{token}'") from exc


def parse_register(token: str) -> int:
    match = REGISTER_RE.fullmatch(token.strip())
    if not match:
        raise AssemblerError(f"invalid register '{token}'")
    register = int(match.group(1))
    if not 0 <= register <= 15:
        raise AssemblerError(f"register r{register} is outside r0-r15")
    return register


def split_operands(text: str) -> list[str]:
    return [part.strip() for part in text.split(",") if part.strip()]


def pass_one(lines: list[str]) -> tuple[dict[str, int], list[SourceInstruction]]:
    labels: dict[str, int] = {}
    instructions: list[SourceInstruction] = []
    pc = 0

    for line_number, raw_line in enumerate(lines, start=1):
        text = strip_comment(raw_line)
        if not text:
            continue

        while ":" in text:
            candidate, remainder = text.split(":", 1)
            label = candidate.strip()
            if not LABEL_RE.fullmatch(label):
                raise AssemblerError(f"line {line_number}: invalid label '{label}'")
            normalized = label.lower()
            if normalized in labels:
                raise AssemblerError(f"line {line_number}: duplicate label '{label}'")
            labels[normalized] = pc
            text = remainder.strip()
            if not text:
                break

        if text:
            instructions.append(SourceInstruction(pc=pc, line_number=line_number, text=text))
            pc += 1

    return labels, instructions


def require_count(mnemonic: str, operands: list[str], expected: int, line_number: int) -> None:
    if len(operands) != expected:
        raise AssemblerError(
            f"line {line_number}: {mnemonic} expects {expected} operand(s), got {len(operands)}"
        )


def resolve_branch_target(token: str, labels: dict[str, int], pc: int) -> int:
    normalized = token.strip().lower()
    if normalized in labels:
        return labels[normalized] - (pc + 1)
    return parse_integer(token)


def encode_source(instruction: SourceInstruction, labels: dict[str, int]) -> int:
    fields = instruction.text.split(None, 1)
    mnemonic = fields[0].upper()
    operand_text = fields[1] if len(fields) == 2 else ""
    operands = split_operands(operand_text)

    if mnemonic == ".WORD":
        require_count(mnemonic, operands, 1, instruction.line_number)
        value = parse_integer(operands[0])
        if not -(1 << 31) <= value <= 0xFFFFFFFF:
            raise AssemblerError(f"line {instruction.line_number}: .word value is outside 32 bits")
        return value & 0xFFFFFFFF

    try:
        opcode = MNEMONIC_TO_OPCODE[mnemonic]
    except KeyError as exc:
        raise AssemblerError(f"line {instruction.line_number}: unknown mnemonic '{mnemonic}'") from exc

    try:
        if opcode == Opcode.NOP:
            require_count(mnemonic, operands, 0, instruction.line_number)
            return encode_nop()

        if opcode in R_OPS:
            require_count(mnemonic, operands, 3, instruction.line_number)
            rd, rs1, rs2 = map(parse_register, operands)
            return encode_r(opcode, rd, rs1, rs2)

        if opcode == Opcode.ADDI:
            require_count(mnemonic, operands, 3, instruction.line_number)
            return encode_i(opcode, parse_register(operands[0]), parse_register(operands[1]), parse_integer(operands[2]))

        if opcode == Opcode.LW:
            require_count(mnemonic, operands, 2, instruction.line_number)
            match = MEMORY_RE.fullmatch(operands[1].replace(" ", ""))
            if not match:
                raise AssemblerError("LW address must use offset(base), for example 4(r2)")
            immediate, base = match.groups()
            return encode_i(opcode, parse_register(operands[0]), parse_register(base), parse_integer(immediate))

        if opcode == Opcode.SW:
            require_count(mnemonic, operands, 2, instruction.line_number)
            match = MEMORY_RE.fullmatch(operands[1].replace(" ", ""))
            if not match:
                raise AssemblerError("SW address must use offset(base), for example 4(r2)")
            immediate, base = match.groups()
            return encode_sb(opcode, parse_register(base), parse_register(operands[0]), parse_integer(immediate))

        if opcode in {Opcode.BEQ, Opcode.BNE}:
            require_count(mnemonic, operands, 3, instruction.line_number)
            offset = resolve_branch_target(operands[2], labels, instruction.pc)
            return encode_sb(opcode, parse_register(operands[0]), parse_register(operands[1]), offset)

    except ValueError as exc:
        if isinstance(exc, AssemblerError):
            raise AssemblerError(f"line {instruction.line_number}: {exc}") from exc
        raise AssemblerError(f"line {instruction.line_number}: {exc}") from exc

    raise AssemblerError(f"line {instruction.line_number}: unsupported opcode '{mnemonic}'")


def assemble_lines(lines: list[str]) -> list[AssembledInstruction]:
    labels, source_instructions = pass_one(lines)
    return [
        AssembledInstruction(
            pc=instruction.pc,
            line_number=instruction.line_number,
            source=instruction.text,
            word=encode_source(instruction, labels),
        )
        for instruction in source_instructions
    ]


def assemble_file(path: Path) -> list[AssembledInstruction]:
    return assemble_lines(path.read_text(encoding="utf-8").splitlines())


def write_hex(path: Path, instructions: list[AssembledInstruction]) -> None:
    path.write_text("".join(f"{instruction.word:08X}\n" for instruction in instructions), encoding="ascii")


def write_listing(path: Path, instructions: list[AssembledInstruction]) -> None:
    lines = ["PC    HEX       BINARY                               SOURCE"]
    for instruction in instructions:
        binary = f"{instruction.word:032b}"
        grouped = "_".join(binary[index : index + 4] for index in range(0, 32, 4))
        lines.append(f"{instruction.pc:04d}  {instruction.word:08X}  {grouped}  {instruction.source}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_csv(path: Path, instructions: list[AssembledInstruction]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["pc", "hex", "binary", "source_line", "source"])
        for instruction in instructions:
            writer.writerow(
                [instruction.pc, f"{instruction.word:08X}", f"{instruction.word:032b}", instruction.line_number, instruction.source]
            )


def write_markdown(path: Path, instructions: list[AssembledInstruction], source_name: str) -> None:
    lines = [
        f"# Assembled machine code: {source_name}",
        "",
        "Generated by `assembler/assembler.py` using the encoding in `isa/isa.py`.",
        "",
        "| PC | Hex word | 32-bit binary | Assembly |",
        "|---:|:---:|:---:|---|",
    ]
    for instruction in instructions:
        lines.append(f"| {instruction.pc} | `{instruction.word:08X}` | `{instruction.word:032b}` | `{instruction.source}` |")
    lines.extend(["", f"Instruction count: **{len(instructions)}**.", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="input assembly file")
    parser.add_argument("-o", "--output", type=Path, required=True, help="hex output file")
    parser.add_argument("--listing", type=Path, help="annotated text listing")
    parser.add_argument("--csv", type=Path, help="CSV listing")
    parser.add_argument("--markdown", type=Path, help="Markdown machine-code table")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    try:
        instructions = assemble_file(args.source)
    except (OSError, AssemblerError) as exc:
        print(f"assembler: error: {exc}", file=sys.stderr)
        return 1

    for path in (args.output, args.listing, args.csv, args.markdown):
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
    write_hex(args.output, instructions)
    if args.listing:
        write_listing(args.listing, instructions)
    if args.csv:
        write_csv(args.csv, instructions)
    if args.markdown:
        write_markdown(args.markdown, instructions, args.source.name)
    print(f"assembled {len(instructions)} instruction(s) -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
