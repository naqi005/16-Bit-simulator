"""
Assembler for the 16-bit Processor — Mano Textbook Notation.

Syntax (Mano style only):
  LDA  SUB       / direct  — label reference
  LDA  I  SUB    / indirect — I flag before operand
  MIN,  DEC  5   / label (comma) + decimal data
  DIF,  HEX  0   / label + hex data
        ORG  100  / set origin
        END       / end of program

Directives:
  ORG  addr      set location counter (decimal)
  DEC  val       store decimal value
  HEX  val       store hexadecimal value
  END            mark end of program

Addressing modes:
  label / addr   Direct    (mode bits = 01)
  I  label       Indirect  (mode bits = 10)
"""

import re

OPCODES = {
    "AND": 0x0, "OR":  0x1, "XOR": 0x2, "ADD": 0x3,
    "SUB": 0x4, "MUL": 0x5, "DIV": 0x6, "PWR": 0x7,
    "LDA": 0x8, "STA": 0x9, "BUN": 0xA, "BSA": 0xB,
    "ISZ": 0xC, "MOD": 0xD, "CMP": 0xE,
}

RRI_BITS = {
    "CLA": 0b1000000000,
    "CLE": 0b0100000000,
    "CMA": 0b0010000000,
    "CME": 0b0001000000,
    "CIR": 0b0000100000,
    "CIL": 0b0000010000,
    "INC": 0b0000001000,
    "HLT": 0b0000000100,
}

IOR_BITS = {
    "INP": 0b1000000000,
    "OUT": 0b0100000000,
    "SKI": 0b0010000000,
    "SKO": 0b0001000000,
    "ION": 0b0000100000,
    "IOF": 0b0000010000,
}

MODE_IMMEDIATE = 0b00
MODE_DIRECT    = 0b01
MODE_INDIRECT  = 0b10
MODE_IO        = 0b11

DIRECTIVES = {"ORG", "DEC", "HEX", "END"}


def _parse_value(token: str) -> int:
    """Parse dec / hex integer literals."""
    token = token.strip()
    if token.startswith(("0x", "0X")):
        return int(token, 16)
    if re.fullmatch(r'-?\d+', token):
        return int(token)
    raise ValueError(f"Cannot parse value: {token!r}")


class AssemblerError(Exception):
    pass


class Assembler:
    def __init__(self):
        self.labels:     dict[str, int]        = {}
        self.program:    list[int]              = []
        self.errors:     list[str]              = []
        self.source_map: list[tuple[int, str]]  = []

    # ═══════════════════════════════════════════
    #  Public API
    # ═══════════════════════════════════════════
    def assemble(self, source: str) -> list[int]:
        self.labels     = {}
        self.program    = []
        self.errors     = []
        self.source_map = []

        lines        = source.splitlines()
        intermediate = self._first_pass(lines)
        if self.errors:
            raise AssemblerError("\n".join(self.errors))
        self._second_pass(intermediate)
        if self.errors:
            raise AssemblerError("\n".join(self.errors))
        return self.program

    # ═══════════════════════════════════════════
    #  Pass 1 — collect labels, build token list
    # ═══════════════════════════════════════════
    def _first_pass(self, lines: list[str]) -> list[tuple]:
        intermediate = []
        lc = 0

        for lineno, raw in enumerate(lines, 1):
            line = raw.strip()

            # strip comment (/)
            if '/' in line:
                line = line[:line.index('/')].strip()

            if not line:
                continue

            # END directive
            if line.upper() == 'END':
                break

            # Extract label — Mano comma style only: MIN,
            label = None
            comma_m = re.match(r'^([A-Za-z_]\w*)\s*,\s*(.*)', line)
            if comma_m:
                label = comma_m.group(1).upper()
                line  = comma_m.group(2).strip()

            if label:
                self.labels[label] = lc

            if not line:
                continue

            parts = line.split()
            first = parts[0].upper()

            # ORG
            if first == 'ORG':
                if len(parts) < 2:
                    self.errors.append(f"Line {lineno}: ORG missing argument")
                    continue
                try:
                    lc = _parse_value(parts[1])
                except ValueError as e:
                    self.errors.append(f"Line {lineno}: {e}")
                continue

            # DEC / HEX
            if first in ('DEC', 'HEX'):
                if len(parts) < 2:
                    self.errors.append(f"Line {lineno}: {first} missing value")
                    continue
                try:
                    raw_val = parts[1]
                    if first == 'HEX':
                        if not raw_val.startswith(('0x', '0X')):
                            raw_val = '0x' + raw_val
                    val = _parse_value(raw_val)
                except ValueError as e:
                    self.errors.append(f"Line {lineno}: {e}")
                    val = 0
                intermediate.append(('DAT', lc, val & 0xFFFF, lineno, raw.strip()))
                lc += 1
                continue

            # Regular instruction
            intermediate.append(('INSTR', lc, line, lineno, raw.strip()))
            lc += 1

        return intermediate

    # ═══════════════════════════════════════════
    #  Pass 2 — encode
    # ═══════════════════════════════════════════
    def _second_pass(self, intermediate: list[tuple]):
        max_addr     = 0
        instructions: dict[int, int] = {}

        for entry in intermediate:
            kind = entry[0]
            addr = entry[1]

            if kind == 'DAT':
                instructions[addr] = entry[2]
                self.source_map.append((addr, entry[4]))
                max_addr = max(max_addr, addr)
                continue

            line   = entry[2]
            lineno = entry[3]
            src    = entry[4]

            try:
                word = self._encode(line, lineno)
            except AssemblerError as e:
                self.errors.append(str(e))
                word = 0

            instructions[addr] = word
            self.source_map.append((addr, src))
            max_addr = max(max_addr, addr)

        if instructions:
            self.program = [0] * (max_addr + 1)
            for addr, word in instructions.items():
                self.program[addr] = word

    # ═══════════════════════════════════════════
    #  Instruction encoder
    # ═══════════════════════════════════════════
    def _encode(self, line: str, lineno: int) -> int:
        parts    = line.split()
        if not parts:
            return 0
        mnemonic = parts[0].upper()

        # Register-Reference
        if mnemonic in RRI_BITS:
            return (MODE_IMMEDIATE << 14) | (0xF << 10) | RRI_BITS[mnemonic]

        # I/O
        if mnemonic in IOR_BITS:
            return (MODE_IO << 14) | (0xF << 10) | IOR_BITS[mnemonic]

        # Memory-Reference
        if mnemonic in OPCODES:
            opcode = OPCODES[mnemonic]
            if len(parts) < 2:
                raise AssemblerError(f"Line {lineno}: {mnemonic} requires an operand")

            # Mano indirect: LDA I LABEL
            if len(parts) >= 3 and parts[1].upper() == 'I':
                addr = self._resolve(parts[2], lineno)
                return (MODE_INDIRECT << 14) | (opcode << 10) | (addr & 0x3FF)

            # Direct (default)
            addr = self._resolve(parts[1], lineno)
            return (MODE_DIRECT << 14) | (opcode << 10) | (addr & 0x3FF)

        raise AssemblerError(f"Line {lineno}: Unknown mnemonic '{mnemonic}'")

    def _resolve(self, token: str, lineno: int) -> int:
        token  = token.strip()
        utoken = token.upper()
        if utoken in self.labels:
            return self.labels[utoken]
        try:
            return _parse_value(token)
        except ValueError:
            raise AssemblerError(
                f"Line {lineno}: Unknown label or value '{token}'")

    # ═══════════════════════════════════════════
    #  Disassembler (memory word → mnemonic)
    # ═══════════════════════════════════════════
    def disassemble(self, word: int) -> str:
        mode    = (word >> 14) & 0x3
        opcode  = (word >> 10) & 0xF
        operand =  word & 0x3FF

        if opcode == 0xF:
            if mode == MODE_IO:
                for name, bits in IOR_BITS.items():
                    if operand & bits:
                        return name
                return f"IOR {operand:03X}"
            if mode == MODE_IMMEDIATE:
                parts = [name for name, bits in RRI_BITS.items() if operand & bits]
                return " ".join(parts) if parts else f"RRI {operand:03X}"
            return f"REG {operand:03X}"

        mnem = next((k for k, v in OPCODES.items() if v == opcode), f"OP{opcode:X}")
        if mode == MODE_DIRECT:
            return f"{mnem} {operand:03X}"
        if mode == MODE_INDIRECT:
            return f"{mnem} I {operand:03X}"
        return f"{mnem} {operand:03X}"

    # ═══════════════════════════════════════════
    #  Assembler listing
    # ═══════════════════════════════════════════
    def listing(self, source: str) -> str:
        program = self.assemble(source)
        lines   = ["Addr  Code   Source                     / Disassembly",
                   "-" * 60]
        for addr, src in self.source_map:
            word   = program[addr] if addr < len(program) else 0
            disasm = self.disassemble(word)
            lines.append(f"{addr:04X}  {word:04X}   {src:<30} / {disasm}")
        return "\n".join(lines)