"""
16-bit Processor Simulator - Interactive CLI
"""

import sys
import os
from processor import Processor
from assembler import Assembler, AssemblerError


HELP_TEXT = """
Commands:
  load <file>         Load and assemble an .asm file
  asm  <code>         Assemble inline code (use ; as line separator)
  run [N]             Run until HLT or N cycles
  step [N]            Execute N steps (default 1)
  reset               Reset processor (keeps memory)
  clear               Reset processor and clear memory
  reg                 Show all registers and flags
  mem [addr] [len]    Dump memory (hex addr, default 0x000 len 32)
  pc <addr>           Set Program Counter
  set <reg> <val>     Set register value (AC, PC, AR, DR, E, etc.)
  input <text>        Load text into input buffer
  output              Show output buffer
  log [N]             Show last N execution log entries (default 20)
  dis [addr] [len]    Disassemble memory range
  watch               Continuously show state (press Enter to step)
  examples            Show example programs
  help                Show this help
  quit / exit         Exit simulator
"""

EXAMPLES = {
    "add_numbers": """\
; Add two numbers and halt
ORG 0x000
    LDA #10        ; AC = 10
    ADD #25        ; AC = 35
    STA 0x100      ; store result at 0x100
    HLT

ORG 0x100
    DAT 0          ; result storage
""",
    "multiply": """\
; Multiply 6 * 7
ORG 0x000
    LDA #6
    MUL #7
    STA 0x100
    HLT

ORG 0x100
    DAT 0
""",
    "loop_sum": """\
; Sum 1+2+3+4+5 = 15
ORG 0x000
    CLA            ; AC = 0
    LDA #0         ; AC = 0

LOOP:
    ADD 0x100      ; AC += counter
    ISZ 0x100      ; increment counter, skip if zero
    BUN LOOP       ; loop back
    STA 0x101      ; store result
    HLT

ORG 0x100
    DAT 1          ; counter starts at 1
    DAT 0          ; result
""",
    "compare": """\
; Compare two values, branch on result
ORG 0x000
    LDA #10
    CMP #20        ; compare AC(10) with 20
    ; L=1 G=0 EQ=0 since 10 < 20
    LDA #0xFF
    AND #0x01      ; clear upper bits
    HLT
""",
    "power": """\
; Compute 3^4 = 81
ORG 0x000
    LDA #3
    PWR #4
    STA 0x100
    HLT

ORG 0x100
    DAT 0
""",
    "modulo": """\
; Compute 17 mod 5 = 2
ORG 0x000
    LDA #17
    MOD #5
    STA 0x100
    HLT

ORG 0x100
    DAT 0
""",
    "fibonacci": """\
; Fibonacci: compute first 8 terms, store at 0x100
ORG 0x000
    CLA
    STA 0x100       ; F(0) = 0
    LDA #1
    STA 0x101       ; F(1) = 1
    LDA 0x100       ; AC = F(0)
    ADD 0x101       ; AC = F(0)+F(1) = 1
    STA 0x102       ; F(2)
    LDA 0x101
    ADD 0x102
    STA 0x103       ; F(3)
    LDA 0x102
    ADD 0x103
    STA 0x104       ; F(4)
    LDA 0x103
    ADD 0x104
    STA 0x105       ; F(5)
    LDA 0x104
    ADD 0x105
    STA 0x106       ; F(6)
    LDA 0x105
    ADD 0x106
    STA 0x107       ; F(7)
    HLT
""",
    "shift_ops": """\
; Demonstrate shift operations
ORG 0x000
    LDA #0x0001    ; AC = 0001
    CIL            ; shift left:  AC = 0002
    CIL            ; AC = 0004
    CIL            ; AC = 0008
    CIR            ; shift right: AC = 0004
    HLT
""",
    "bsa_return": """\
; Subroutine call and return using BSA
ORG 0x000
    LDA #5
    BSA DOUBLE     ; call subroutine
    HLT

DOUBLE:
    DAT 0          ; return address stored here
    ADD #5         ; double the value (5+5=10)
    BUN [DOUBLE]   ; return (indirect jump through DOUBLE)
""",
    "isz_counter": """\
; Use ISZ to count down from -5 (skip when hits 0)
ORG 0x000
    LDA #0         ; AC = 0
WAIT:
    ISZ 0x100      ; increment M[0x100], skip next if zero
    BUN WAIT
    LDA #0x00FF    ; skip happened, execution here
    HLT

ORG 0x100
    DAT 0xFFFB     ; -5 in two's complement
""",
}


def parse_addr(s: str) -> int:
    s = s.strip()
    if s.startswith("0x") or s.startswith("0X"):
        return int(s, 16)
    return int(s)


def format_word_binary(word: int) -> str:
    b = f"{word:016b}"
    return f"{b[0:2]} {b[2:6]} {b[6:]}"  # mode | opcode | operand


class SimulatorCLI:
    def __init__(self):
        self.cpu = Processor()
        self.asm = Assembler()
        self.current_file = None

    def run(self):
        print("=" * 60)
        print("  16-Bit Processor Simulator")
        print("  CE-222 COAL Project")
        print("=" * 60)
        print("Type 'help' for commands, 'examples' to see sample programs")
        print()

        while True:
            try:
                raw = input("sim> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting.")
                break

            if not raw:
                continue

            parts = raw.split()
            cmd = parts[0].lower()
            args = parts[1:]

            try:
                self._dispatch(cmd, args, raw)
            except Exception as e:
                print(f"Error: {e}")

    def _dispatch(self, cmd: str, args: list, raw: str):
        if cmd in ("quit", "exit", "q"):
            print("Bye.")
            sys.exit(0)

        elif cmd == "help":
            print(HELP_TEXT)

        elif cmd == "examples":
            self._cmd_examples(args)

        elif cmd == "load":
            self._cmd_load(args)

        elif cmd == "asm":
            self._cmd_asm(raw)

        elif cmd == "run":
            self._cmd_run(args)

        elif cmd == "step":
            self._cmd_step(args)

        elif cmd == "reset":
            self.cpu.reset()
            print("Processor reset (memory preserved).")

        elif cmd == "clear":
            self.cpu.reset()
            self.cpu.memory = [0] * Processor.MEMORY_SIZE
            print("Processor and memory cleared.")

        elif cmd == "reg":
            print(self.cpu.dump_registers())

        elif cmd == "mem":
            self._cmd_mem(args)

        elif cmd == "pc":
            if args:
                self.cpu.PC = parse_addr(args[0]) & 0x3FF
                print(f"PC set to {self.cpu.PC:04X}")
            else:
                print(f"PC = {self.cpu.PC:04X}")

        elif cmd == "set":
            self._cmd_set(args)

        elif cmd == "input":
            text = raw[len("input"):].strip()
            self.cpu.input_buffer.extend(list(text))
            self.cpu.FGI = 1
            print(f"Input buffer: {self.cpu.input_buffer}")

        elif cmd == "output":
            out = "".join(self.cpu.output_buffer)
            print(f"Output buffer: {out!r}")

        elif cmd == "log":
            n = int(args[0]) if args else 20
            log = self.cpu.execution_log[-n:]
            print("\n".join(log) if log else "(empty log)")

        elif cmd == "dis":
            self._cmd_dis(args)

        elif cmd == "watch":
            self._cmd_watch()

        else:
            print(f"Unknown command: {cmd!r}. Type 'help'.")

    def _cmd_load(self, args: list):
        if not args:
            print("Usage: load <file.asm>")
            return
        path = " ".join(args)
        if not os.path.exists(path):
            print(f"File not found: {path}")
            return
        with open(path, "r") as f:
            source = f.read()
        self._assemble_and_load(source, path)

    def _cmd_asm(self, raw: str):
        code = raw[3:].strip()
        if not code:
            print("Usage: asm <code>  (use semicolons as line separators)")
            return
        source = code.replace(";", "\n")
        self._assemble_and_load(source, "<inline>")

    def _assemble_and_load(self, source: str, name: str):
        try:
            program = self.asm.assemble(source)
        except AssemblerError as e:
            print(f"Assembly error:\n{e}")
            return

        self.cpu.reset()
        self.cpu.load_program(program, 0)
        self.current_file = name
        print(f"Assembled {len(program)} words from {name}")
        print(f"PC set to {self.cpu.PC:04X}")
        print()
        # Print listing
        try:
            listing = self.asm.listing(source)
            print(listing)
        except Exception:
            pass

    def _cmd_run(self, args: list):
        max_cycles = int(args[0]) if args else 100000
        print(f"Running (max {max_cycles} cycles)...")
        result = self.cpu.run(max_cycles)
        print(result)
        print(self.cpu.dump_registers())
        out = "".join(self.cpu.output_buffer)
        if out:
            print(f"Output: {out!r}")

    def _cmd_step(self, args: list):
        n = int(args[0]) if args else 1
        for i in range(n):
            if self.cpu.halted:
                print("Processor is halted. Use 'reset' to restart.")
                break
            alive = self.cpu.step()
            # Show last log entry
            if self.cpu.execution_log:
                print(self.cpu.execution_log[-1])
            if not alive:
                print("Halted.")
                break
        self._print_short_state()

    def _cmd_mem(self, args: list):
        start = parse_addr(args[0]) if args else 0
        length = int(args[1], 0) if len(args) > 1 else 32
        print(self.cpu.dump_memory(start, length))

    def _cmd_set(self, args: list):
        if len(args) < 2:
            print("Usage: set <reg> <value>")
            return
        reg = args[0].upper()
        val = parse_addr(args[1])
        reg_map = {
            "PC": "PC", "AR": "AR", "IR": "IR", "DR": "DR",
            "AC": "AC", "INPR": "INPR", "OUTR": "OUTR", "SC": "SC",
            "E": "E", "L": "L", "G": "G", "EQ": "EQ",
            "FGI": "FGI", "FGO": "FGO", "IEN": "IEN", "R": "R",
        }
        if reg in reg_map:
            setattr(self.cpu, reg_map[reg], val)
            print(f"{reg} = {val:04X}")
        else:
            print(f"Unknown register: {reg}")

    def _cmd_dis(self, args: list):
        start = parse_addr(args[0]) if args else self.cpu.PC
        length = int(args[1], 0) if len(args) > 1 else 16
        print(f"\nDisassembly [{start:03X} - {start+length-1:03X}]:")
        print(f"{'Addr':>4}  {'Word':>4}  {'Binary':>18}  {'Disassembly':<20}")
        print("-" * 58)
        for i in range(length):
            addr = start + i
            if addr >= Processor.MEMORY_SIZE:
                break
            word = self.cpu.memory[addr]
            disasm = self.asm.disassemble(word)
            marker = " <" if addr == self.cpu.PC else "  "
            print(f"{addr:04X}  {word:04X}  {format_word_binary(word)}  {disasm}{marker}")

    def _cmd_watch(self):
        print("Watch mode: Press Enter to step, 'q' to quit.")
        while not self.cpu.halted:
            self._print_short_state()
            try:
                inp = input("[Enter=step, q=quit] ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                break
            if inp == "q":
                break
            self.cpu.step()
            if self.cpu.execution_log:
                print(self.cpu.execution_log[-1])
        self._print_short_state()

    def _cmd_examples(self, args: list):
        if not args:
            print("Available examples:")
            for name in EXAMPLES:
                print(f"  examples {name}")
            return
        name = args[0].lower()
        if name not in EXAMPLES:
            print(f"Unknown example: {name}")
            return
        source = EXAMPLES[name]
        print(f"\n--- Example: {name} ---")
        print(source)
        run = input("Load and run this example? [y/N] ").strip().lower()
        if run == "y":
            self._assemble_and_load(source, f"example:{name}")
            self._cmd_run([])

    def _print_short_state(self):
        s = self.cpu.get_state()
        word = self.cpu.memory[s["PC"]] if s["PC"] < Processor.MEMORY_SIZE else 0
        disasm = self.asm.disassemble(word)
        print(
            f"  PC={s['PC']:04X}  AC={s['AC']:04X}  AR={s['AR']:04X}  DR={s['DR']:04X}"
            f"  E={s['E']} L={s['L']} G={s['G']} EQ={s['EQ']}"
            f"  | next: {disasm}"
        )


if __name__ == "__main__":
    cli = SimulatorCLI()
    if len(sys.argv) > 1:
        # Auto-load file if given as argument
        path = sys.argv[1]
        if os.path.exists(path):
            with open(path) as f:
                src = f.read()
            try:
                prog = cli.asm.assemble(src)
                cli.cpu.load_program(prog, 0)
                cli.current_file = path
                print(f"Loaded {path} ({len(prog)} words)")
            except AssemblerError as e:
                print(f"Assembly error: {e}")
    cli.run()