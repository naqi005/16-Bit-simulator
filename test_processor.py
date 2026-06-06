"""Tests for the 16-bit processor simulator."""

import sys
sys.path.insert(0, ".")

from processor import Processor
from assembler import Assembler, AssemblerError


def run_program(source: str, input_text: str = "", max_cycles: int = 10000) -> Processor:
    asm = Assembler()
    cpu = Processor()
    program = asm.assemble(source)
    cpu.load_program(program, 0)
    if input_text:
        cpu.input_buffer = list(input_text)
        cpu.FGI = 1
    cpu.run(max_cycles)
    return cpu


def test(name: str, condition: bool):
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {name}")
    return condition


def run_all_tests():
    total = 0
    passed = 0

    def check(name, cond):
        nonlocal total, passed
        total += 1
        if test(name, cond):
            passed += 1

    print("=" * 55)
    print("  16-BIT PROCESSOR SIMULATOR TEST SUITE")
    print("=" * 55)

    # ── Arithmetic ──────────────────────────────────────────
    print("\n[1] Arithmetic Operations")

    cpu = run_program("LDA #15\nADD #20\nHLT")
    check("ADD immediate: 15+20=35", cpu.AC == 35)

    cpu = run_program("LDA #50\nSUB #13\nHLT")
    check("SUB immediate: 50-13=37", cpu.AC == 37)

    cpu = run_program("LDA #6\nMUL #7\nHLT")
    check("MUL immediate: 6*7=42", cpu.AC == 42)

    cpu = run_program("LDA #100\nDIV #4\nHLT")
    check("DIV immediate: 100/4=25", cpu.AC == 25)

    cpu = run_program("LDA #17\nMOD #5\nHLT")
    check("MOD immediate: 17 mod 5=2", cpu.AC == 2)

    cpu = run_program("LDA #2\nPWR #8\nHLT")
    check("PWR immediate: 2^8=256", cpu.AC == 256)

    cpu = run_program("LDA #3\nPWR #4\nHLT")
    check("PWR immediate: 3^4=81", cpu.AC == 81)

    # ── Carry flag ──────────────────────────────────────────
    print("\n[2] Carry/Overflow Flags")

    # Max 10-bit immediate = 0x3FF; store larger values in memory
    cpu = run_program(
        "ORG 0x000\nLDA 0x100\nADD 0x101\nHLT\n"
        "ORG 0x100\nDAT 0xFFFF\nDAT 1"
    )
    check("ADD overflow sets E=1 (0xFFFF+1)", cpu.E == 1 and cpu.AC == 0)

    cpu = run_program("LDA #5\nSUB #10\nHLT")
    check("SUB underflow sets E=1", cpu.E == 1)

    # ── Logic ───────────────────────────────────────────────
    print("\n[3] Logic Operations")

    cpu = run_program("LDA #0xFF\nAND #0x0F\nHLT")
    check("AND: 0xFF & 0x0F = 0x0F", cpu.AC == 0x0F)

    cpu = run_program("LDA #0xF0\nOR #0x0F\nHLT")
    check("OR:  0xF0 | 0x0F = 0xFF", cpu.AC == 0xFF)

    cpu = run_program("LDA #0xFF\nXOR #0xAA\nHLT")
    check("XOR: 0xFF ^ 0xAA = 0x55", cpu.AC == 0x55)

    # ── Register-Reference ─────────────────────────────────
    print("\n[4] Register-Reference Instructions")

    cpu = run_program("LDA #0xABCD\nCLA\nHLT")
    check("CLA: AC = 0", cpu.AC == 0)

    cpu = run_program("LDA #0x00FF\nCMA\nHLT")
    check("CMA: complement 0x00FF = 0xFF00", cpu.AC == 0xFF00)

    cpu = run_program("LDA #5\nINC\nHLT")
    check("INC: 5+1=6", cpu.AC == 6)

    cpu = run_program("LDA #0x0001\nCIL\nHLT")
    check("CIL: shift left 0x0001 -> 0x0002", cpu.AC == 0x0002)

    cpu = run_program("LDA #0x0004\nCIR\nHLT")
    check("CIR: shift right 0x0004 -> 0x0002", cpu.AC == 0x0002)

    # Shift 0x0001 right: AC=0, E=1 (LSB shifts into E)
    cpu = run_program("LDA #1\nCIR\nHLT")
    check("CIR: shift 0x0001 right -> AC=0x0000 E=1", cpu.AC == 0x0000 and cpu.E == 1)

    # ── Comparison ─────────────────────────────────────────
    print("\n[5] Comparison (CMP)")

    cpu = run_program("LDA #10\nCMP #20\nHLT")
    check("CMP: 10 < 20  ->L=1 G=0 EQ=0", cpu.L == 1 and cpu.G == 0 and cpu.EQ == 0)

    cpu = run_program("LDA #20\nCMP #10\nHLT")
    check("CMP: 20 > 10  ->G=1 L=0 EQ=0", cpu.G == 1 and cpu.L == 0 and cpu.EQ == 0)

    cpu = run_program("LDA #15\nCMP #15\nHLT")
    check("CMP: 15 = 15  ->EQ=1 L=0 G=0", cpu.EQ == 1 and cpu.L == 0 and cpu.G == 0)

    # ── Memory operations ──────────────────────────────────
    print("\n[6] Memory: LDA / STA")

    cpu = run_program(
        "ORG 0x000\nLDA #99\nSTA 0x100\nCLA\nLDA 0x100\nHLT\n"
        "ORG 0x100\nDAT 0"
    )
    check("STA/LDA direct: store 99, reload", cpu.AC == 99)

    cpu = run_program(
        "ORG 0x000\nLDA #77\nSTA 0x101\nLDA [0x100]\nHLT\n"
        "ORG 0x100\nDAT 0x101\nDAT 0"
    )
    check("LDA indirect: pointer 0x100->0x101 = 77", cpu.AC == 77)

    # ── BUN ────────────────────────────────────────────────
    print("\n[7] Control Flow (BUN/BSA/ISZ)")

    cpu = run_program(
        "ORG 0x000\n"
        "LDA #1\nBUN SKIP\nLDA #99\n"
        "SKIP:\nADD #5\nHLT"
    )
    check("BUN: skips LDA #99, AC=1+5=6", cpu.AC == 6)

    # ISZ test: counter from -3, skip at 0
    cpu = run_program(
        "ORG 0x000\n"
        "CLA\n"
        "LOOP:\nINC\nISZ 0x100\nBUN LOOP\nHLT\n"
        "ORG 0x100\nDAT 0xFFFD"   # -3 in two's complement
    )
    check("ISZ: loop 3 times, AC=3", cpu.AC == 3)

    # BSA subroutine return
    cpu = run_program(
        "ORG 0x000\n"
        "LDA #10\n"
        "BSA SUB\n"
        "HLT\n"
        "SUB:\nDAT 0\n"
        "ADD #5\n"
        "BUN [SUB]\n"
    )
    check("BSA: subroutine adds 5, AC=15", cpu.AC == 15)

    # ── Addressing modes ──────────────────────────────────
    print("\n[8] Addressing Modes")

    cpu = run_program("LDA #42\nHLT")
    check("Immediate: LDA #42 -> AC=42", cpu.AC == 42)

    cpu = run_program(
        "ORG 0x000\nLDA 0x100\nHLT\n"
        "ORG 0x100\nDAT 0xBEEF"
    )
    check("Direct: LDA 0x100 -> AC=0xBEEF", cpu.AC == 0xBEEF)

    cpu = run_program(
        "ORG 0x000\nLDA [0x100]\nHLT\n"
        "ORG 0x100\nDAT 0x101\n"
        "ORG 0x101\nDAT 0xCAFE"
    )
    check("Indirect: LDA [0x100] -> M[0x101]=0xCAFE", cpu.AC == 0xCAFE)

    # ── I/O ───────────────────────────────────────────────
    print("\n[9] I/O Instructions")

    cpu = run_program("INP\nHLT", input_text="A")
    check("INP: input 'A' (0x41) into AC", cpu.AC & 0xFF == ord("A"))

    cpu = run_program("LDA #65\nOUT\nHLT")
    check("OUT: output AC[7:0]=0x41='A'", "".join(cpu.output_buffer) == "A")

    # ── Division example from PDF ─────────────────────────
    print("\n[10] PDF Examples Verification")

    cpu = run_program("LDA #11\nDIV #3\nHLT")
    check("PDF DIV: 11 / 3 = 3 (quotient)", cpu.AC == 3)

    cpu = run_program("LDA #11\nMOD #3\nHLT")
    check("PDF MOD: 11 mod 3 = 2", cpu.AC == 2)

    cpu = run_program("LDA #11\nMUL #13\nHLT")
    check("PDF MUL: 11*13=143 (lower 16 bits)", cpu.AC == 143)

    cpu = run_program("LDA #2\nPWR #4\nHLT")
    check("PDF PWR: 2^4=16", cpu.AC == 16)

    cpu = run_program("LDA #14\nMOD #3\nHLT")
    check("PDF MOD: 14 mod 3 = 2", cpu.AC == 2)

    cpu = run_program("LDA #15\nSUB #6\nHLT")
    check("PDF SUB: 15-6=9", cpu.AC == 9)

    # ── Fibonacci ─────────────────────────────────────────
    print("\n[11] Fibonacci Sequence")
    fib_src = """
ORG 0x000
    CLA
    STA 0x100
    LDA #1
    STA 0x101
    LDA 0x100
    ADD 0x101
    STA 0x102
    LDA 0x101
    ADD 0x102
    STA 0x103
    LDA 0x102
    ADD 0x103
    STA 0x104
    HLT
ORG 0x100
    DAT 0
    DAT 0
    DAT 0
    DAT 0
    DAT 0
"""
    cpu = run_program(fib_src)
    expected = [0, 1, 1, 2, 3]
    actual = [cpu.memory[0x100 + i] for i in range(5)]
    check("Fibonacci F(0..4) = [0,1,1,2,3]", actual == expected)

    # ── Assembler ─────────────────────────────────────────
    print("\n[12] Assembler Tests")

    asm = Assembler()
    prog = asm.assemble("LDA #42\nHLT")
    check("Assembler: 2 words generated", len(prog) == 2)

    asm2 = Assembler()
    try:
        asm2.assemble("BADOP 42")
        check("Assembler: unknown mnemonic raises error", False)
    except AssemblerError:
        check("Assembler: unknown mnemonic raises error", True)

    asm3 = Assembler()
    prog3 = asm3.assemble("ORG 0x010\nLDA #1\nHLT")
    check("Assembler: ORG directive sets address", len(prog3) == 0x12)

    # ── Halted state ──────────────────────────────────────
    print("\n[13] Processor Control")

    cpu = run_program("LDA #5\nHLT\nLDA #99")
    check("HLT stops execution before LDA #99", cpu.AC == 5)

    cpu2 = Processor()
    cpu2.reset()
    check("Reset: AC=0 after reset", cpu2.AC == 0 and cpu2.PC == 0)

    # ── Summary ───────────────────────────────────────────
    print()
    print("=" * 55)
    print(f"  Results: {passed}/{total} tests passed")
    if passed == total:
        print("  ALL TESTS PASSED!")
    else:
        print(f"  {total - passed} test(s) FAILED")
    print("=" * 55)
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)