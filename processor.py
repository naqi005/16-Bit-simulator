"""
16-bit Processor Simulator
Architecture based on enhanced Mano Machine design.

Instruction Format (16 bits):
  [15:14] - Address Mode (2 bits): 00=Immediate, 01=Direct, 10=Indirect, 11=I/O
  [13:10] - Opcode (4 bits)
  [9:0]   - Address/Operand (10 bits)
"""

class Processor:
    MEMORY_SIZE = 1024

    # Opcodes
    OP_AND = 0x0
    OP_OR  = 0x1
    OP_XOR = 0x2
    OP_ADD = 0x3
    OP_SUB = 0x4
    OP_MUL = 0x5
    OP_DIV = 0x6
    OP_PWR = 0x7
    OP_LDA = 0x8
    OP_STA = 0x9
    OP_BUN = 0xA
    OP_BSA = 0xB
    OP_ISZ = 0xC
    OP_MOD = 0xD
    OP_CMP = 0xE
    OP_REG = 0xF  # RRI or IOR depending on addr mode

    # Addressing modes
    MODE_IMMEDIATE = 0b00
    MODE_DIRECT    = 0b01
    MODE_INDIRECT  = 0b10
    MODE_IO        = 0b11

    # Register-Reference bit masks (bits 9-0 of instruction)
    RRI_CLA = 0b1000000000
    RRI_CLE = 0b0100000000
    RRI_CMA = 0b0010000000
    RRI_CME = 0b0001000000
    RRI_CIR = 0b0000100000
    RRI_CIL = 0b0000010000
    RRI_INC = 0b0000001000
    RRI_HLT = 0b0000000100

    # I/O instruction bit masks
    IOR_INP = 0b1000000000
    IOR_OUT = 0b0100000000
    IOR_SKI = 0b0010000000
    IOR_SKO = 0b0001000000
    IOR_ION = 0b0000100000
    IOR_IOF = 0b0000010000

    def __init__(self):
        self.memory = [0] * self.MEMORY_SIZE
        self.reset()
        self.halted = False
        self.input_buffer = []
        self.output_buffer = []
        self.execution_log = []
        self.cycle_count = 0

    def reset(self):
        # Registers
        self.PC  = 0      # Program Counter (10-bit)
        self.AR  = 0      # Address Register (10-bit)
        self.IR  = 0      # Instruction Register (16-bit)
        self.DR  = 0      # Data Register (16-bit)
        self.AC  = 0      # Accumulator (16-bit)
        self.INPR = 0     # Input Register (8-bit)
        self.OUTR = 0     # Output Register (8-bit)
        self.SC  = 0      # Sequence Counter (4-bit)

        # Flags
        self.E   = 0      # Carry/Extended flag
        self.L   = 0      # Less-than flag
        self.G   = 0      # Greater-than flag
        self.EQ  = 0      # Equal flag
        self.FGI = 1      # Input Flag (1 = ready)
        self.FGO = 1      # Output Flag (1 = ready)
        self.IEN = 0      # Interrupt Enable
        self.R   = 0      # Interrupt state

        self.halted = False
        self.cycle_count = 0
        self.execution_log = []

    def load_program(self, program: list, start_address: int = 0):
        for i, word in enumerate(program):
            if start_address + i < self.MEMORY_SIZE:
                self.memory[start_address + i] = word & 0xFFFF
        self.PC = start_address

    def _mask16(self, val: int) -> int:
        return val & 0xFFFF

    def _mask10(self, val: int) -> int:
        return val & 0x3FF

    def _to_signed16(self, val: int) -> int:
        val = val & 0xFFFF
        return val if val < 0x8000 else val - 0x10000

    def _log(self, msg: str):
        self.execution_log.append(f"[Cycle {self.cycle_count}] {msg}")

    def _get_effective_address(self, mode: int, addr: int) -> int:
        if mode == self.MODE_IMMEDIATE:
            return addr  # operand IS the value (used directly, not as address)
        elif mode == self.MODE_DIRECT:
            return addr
        elif mode == self.MODE_INDIRECT:
            return self._mask10(self.memory[addr])
        return addr

    def _get_operand(self, mode: int, addr: int) -> int:
        if mode == self.MODE_IMMEDIATE:
            return addr & 0xFFFF
        ea = self._get_effective_address(mode, addr)
        return self.memory[ea]

    def fetch(self):
        self.AR = self.PC
        self.IR = self.memory[self.AR]
        self.PC = self._mask10(self.PC + 1)
        self.SC = 1

    def decode_and_execute(self):
        instr = self.IR
        mode   = (instr >> 14) & 0x3
        opcode = (instr >> 10) & 0xF
        operand = instr & 0x3FF

        self._log(f"PC={self.PC:03X} IR={instr:04X} mode={mode:02b} op={opcode:04b} oper={operand:03X}")

        if opcode == self.OP_REG:
            if mode == self.MODE_IO:
                self._execute_io(operand)
            elif mode == self.MODE_IMMEDIATE:
                self._execute_rri(operand)
            else:
                self._log(f"Unknown REG mode {mode}")
            return

        self._execute_mri(opcode, mode, operand)

    def _execute_mri(self, opcode: int, mode: int, addr: int):
        if opcode == self.OP_AND:
            operand = self._get_operand(mode, addr)
            self.AC = self._mask16(self.AC & operand)
            self._log(f"AND  AC={self.AC:04X}")

        elif opcode == self.OP_OR:
            operand = self._get_operand(mode, addr)
            self.AC = self._mask16(self.AC | operand)
            self._log(f"OR   AC={self.AC:04X}")

        elif opcode == self.OP_XOR:
            operand = self._get_operand(mode, addr)
            self.AC = self._mask16(self.AC ^ operand)
            self._log(f"XOR  AC={self.AC:04X}")

        elif opcode == self.OP_ADD:
            operand = self._get_operand(mode, addr)
            result = self.AC + operand
            self.E = 1 if result > 0xFFFF else 0
            self.AC = self._mask16(result)
            self._log(f"ADD  AC={self.AC:04X} E={self.E}")

        elif opcode == self.OP_SUB:
            operand = self._get_operand(mode, addr)
            result = self.AC - operand
            self.E = 1 if result < 0 else 0
            self.AC = self._mask16(result)
            self._log(f"SUB  AC={self.AC:04X} E={self.E}")

        elif opcode == self.OP_MUL:
            operand = self._get_operand(mode, addr)
            result = self.AC * operand
            self.E = 1 if result > 0xFFFF else 0
            self.AC = self._mask16(result)
            self._log(f"MUL  AC={self.AC:04X} (full={result})")

        elif opcode == self.OP_DIV:
            operand = self._get_operand(mode, addr)
            if operand == 0:
                self._log("DIV  by zero! Halting.")
                self.halted = True
                return
            self.AC = self._mask16(self.AC // operand)
            self.E = 0
            self._log(f"DIV  AC={self.AC:04X}")

        elif opcode == self.OP_PWR:
            operand = self._get_operand(mode, addr)
            result = pow(self.AC, operand)
            self.E = 1 if result > 0xFFFF else 0
            self.AC = self._mask16(result)
            self._log(f"PWR  AC={self.AC:04X} (full={result})")

        elif opcode == self.OP_LDA:
            operand = self._get_operand(mode, addr)
            self.AC = self._mask16(operand)
            self._log(f"LDA  AC={self.AC:04X}")

        elif opcode == self.OP_STA:
            if mode == self.MODE_IMMEDIATE:
                self._log("STA  N/A in immediate mode")
                return
            ea = self._get_effective_address(mode, addr)
            self.memory[ea] = self.AC
            self._log(f"STA  M[{ea:03X}]={self.AC:04X}")

        elif opcode == self.OP_BUN:
            if mode == self.MODE_IMMEDIATE:
                self._log("BUN  N/A in immediate mode")
                return
            ea = self._get_effective_address(mode, addr)
            self.PC = self._mask10(ea)
            self.SC = 0
            self._log(f"BUN  PC={self.PC:03X}")

        elif opcode == self.OP_BSA:
            if mode == self.MODE_IMMEDIATE:
                self._log("BSA  N/A in immediate mode")
                return
            ea = self._get_effective_address(mode, addr)
            self.AR = ea
            self.memory[self.AR] = self.PC
            self.AR = self._mask10(self.AR + 1)
            self.PC = self.AR
            self.SC = 0
            self._log(f"BSA  PC={self.PC:03X} return stored at M[{ea:03X}]")

        elif opcode == self.OP_ISZ:
            if mode == self.MODE_IMMEDIATE:
                self._log("ISZ  N/A in immediate mode")
                return
            ea = self._get_effective_address(mode, addr)
            self.DR = self._mask16(self.memory[ea] + 1)
            self.memory[ea] = self.DR
            if self.DR == 0:
                self.PC = self._mask10(self.PC + 1)
            self.SC = 0
            self._log(f"ISZ  M[{ea:03X}]={self.DR:04X} PC={self.PC:03X}")

        elif opcode == self.OP_MOD:
            operand = self._get_operand(mode, addr)
            if operand == 0:
                self._log("MOD  by zero! Halting.")
                self.halted = True
                return
            self.AC = self._mask16(self.AC % operand)
            self._log(f"MOD  AC={self.AC:04X}")

        elif opcode == self.OP_CMP:
            operand = self._get_operand(mode, addr)
            self.L = 1 if self.AC < operand else 0
            self.G = 1 if self.AC > operand else 0
            self.EQ = 1 if self.AC == operand else 0
            self._log(f"CMP  L={self.L} G={self.G} EQ={self.EQ}")

    def _execute_rri(self, operand: int):
        if operand & self.RRI_CLA:
            self.AC = 0
            self._log("CLA  AC=0000")

        if operand & self.RRI_CLE:
            self.E = 0
            self._log("CLE  E=0")

        if operand & self.RRI_CMA:
            self.AC = self._mask16(~self.AC)
            self._log(f"CMA  AC={self.AC:04X}")

        if operand & self.RRI_CME:
            self.E = 1 - self.E
            self._log(f"CME  E={self.E}")

        if operand & self.RRI_CIR:
            # Circular shift right: E -> AC[15], AC[0] -> E, AC >> 1
            lsb = self.AC & 1
            self.AC = ((self.E << 15) | (self.AC >> 1)) & 0xFFFF
            self.E = lsb
            self._log(f"CIR  AC={self.AC:04X} E={self.E}")

        if operand & self.RRI_CIL:
            # Circular shift left: E -> AC[0], AC[15] -> E, AC << 1
            msb = (self.AC >> 15) & 1
            self.AC = (((self.AC << 1) & 0xFFFF) | self.E)
            self.E = msb
            self._log(f"CIL  AC={self.AC:04X} E={self.E}")

        if operand & self.RRI_INC:
            self.AC = self._mask16(self.AC + 1)
            self._log(f"INC  AC={self.AC:04X}")

        if operand & self.RRI_HLT:
            self.halted = True
            self._log("HLT  Processor halted")

    def _execute_io(self, operand: int):
        if operand & self.IOR_INP:
            if self.input_buffer:
                self.INPR = ord(self.input_buffer.pop(0)) & 0xFF
            self.AC = (self.AC & 0xFF00) | self.INPR
            self.FGI = 0
            self._log(f"INP  AC(7-0)={self.INPR:02X} FGI=0")

        if operand & self.IOR_OUT:
            self.OUTR = self.AC & 0xFF
            self.output_buffer.append(chr(self.OUTR))
            self.FGO = 0
            self._log(f"OUT  OUTR={self.OUTR:02X} ('{chr(self.OUTR)}') FGO=0")

        if operand & self.IOR_SKI:
            if self.FGI == 1:
                self.PC = self._mask10(self.PC + 1)
            self._log(f"SKI  FGI={self.FGI} PC={self.PC:03X}")

        if operand & self.IOR_SKO:
            if self.FGO == 1:
                self.PC = self._mask10(self.PC + 1)
            self._log(f"SKO  FGO={self.FGO} PC={self.PC:03X}")

        if operand & self.IOR_ION:
            self.IEN = 1
            self._log("ION  IEN=1")

        if operand & self.IOR_IOF:
            self.IEN = 0
            self._log("IOF  IEN=0")

    def step(self) -> bool:
        if self.halted:
            return False
        self.cycle_count += 1
        self.fetch()
        self.decode_and_execute()
        return not self.halted

    def run(self, max_cycles: int = 100000) -> str:
        cycles = 0
        while not self.halted and cycles < max_cycles:
            self.step()
            cycles += 1
        if cycles >= max_cycles:
            return f"Stopped after {max_cycles} cycles (possible infinite loop)"
        return f"Halted after {cycles} cycles"

    def get_state(self) -> dict:
        return {
            "PC":   self.PC,
            "AR":   self.AR,
            "IR":   self.IR,
            "DR":   self.DR,
            "AC":   self.AC,
            "INPR": self.INPR,
            "OUTR": self.OUTR,
            "SC":   self.SC,
            "E":    self.E,
            "L":    self.L,
            "G":    self.G,
            "EQ":   self.EQ,
            "FGI":  self.FGI,
            "FGO":  self.FGO,
            "IEN":  self.IEN,
            "R":    self.R,
            "halted": self.halted,
            "cycles": self.cycle_count,
        }

    def dump_registers(self) -> str:
        s = self.get_state()
        lines = [
            "=" * 50,
            "  REGISTER STATE",
            "=" * 50,
            f"  PC  = {s['PC']:04X}  ({s['PC']:>5d})   AR  = {s['AR']:04X}  ({s['AR']:>5d})",
            f"  IR  = {s['IR']:04X}  ({s['IR']:>5d})   DR  = {s['DR']:04X}  ({s['DR']:>5d})",
            f"  AC  = {s['AC']:04X}  ({s['AC']:>5d})   SC  = {s['SC']:04X}",
            f"  INPR= {s['INPR']:02X}             OUTR= {s['OUTR']:02X}",
            "-" * 50,
            "  FLAGS",
            f"  E={s['E']}  L={s['L']}  G={s['G']}  EQ={s['EQ']}",
            f"  FGI={s['FGI']}  FGO={s['FGO']}  IEN={s['IEN']}  R={s['R']}",
            "-" * 50,
            f"  Cycles: {s['cycles']}   Halted: {s['halted']}",
            "=" * 50,
        ]
        return "\n".join(lines)

    def dump_memory(self, start: int = 0, length: int = 32) -> str:
        lines = [f"Memory [{start:03X} - {start+length-1:03X}]:"]
        for i in range(0, length, 8):
            addr = start + i
            vals = " ".join(f"{self.memory[addr+j]:04X}" for j in range(8) if addr+j < self.MEMORY_SIZE)
            lines.append(f"  {addr:03X}: {vals}")
        return "\n".join(lines)