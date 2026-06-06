# 16-Bit Processor Simulator

A fully functional 16-bit CPU simulator built for the **CE-222 Computer Organization and Assembly Language (COAL)** course at **FCSE, GIKI**.

Implements the **Mano Machine** architecture from the textbook *Computer System Architecture* by M. Morris Mano.

---

## Features

- **Two-pass assembler** with Mano textbook notation
- **Full CPU simulation** — fetch, decode, execute cycle
- **Modern dark IDE-style GUI** built with Python tkinter
- **Memory view** — 1024 × 16-bit words with address, hex, decimal, and disassembly columns
- **Register panel** — PC, AR, IR, DR, AC, INPR, OUTR with live hex and decimal display
- **Syntax-highlighted code editor** with line numbers
- **Step / Run / Stop / Reset** execution controls
- **6 built-in example programs**

---

## Architecture

| Property | Value |
|---|---|
| Word size | 16 bits |
| Memory | 1024 words |
| Address bits | 10 bits |
| Addressing modes | Direct, Indirect |

### Instruction Set

**Memory-Reference (MRI):** `AND OR XOR ADD SUB MUL DIV PWR LDA STA BUN BSA ISZ MOD CMP`

**Register-Reference (RRI):** `CLA CLE CMA CME CIR CIL INC HLT`

**I/O:** `INP OUT SKI SKO ION IOF`

**Directives:** `ORG DEC HEX END`

---

## Assembly Syntax (Mano Notation)

```
        ORG  0          / Set origin to address 0
        LDA  NUM        / Load AC from memory[NUM]
        ADD  VAL        / AC = AC + memory[VAL]
        STA  RES        / Store AC into memory[RES]
        HLT             / Halt
NUM,    DEC  25         / Label with decimal value
VAL,    DEC  10
RES,    HEX  0          / Label with hex value
        END
```

- Labels end with a **comma**: `LABEL,`
- Comments start with **`/`**
- Indirect addressing: place **`I`** between mnemonic and operand — `LDA I PTR`

---

## Project Structure

```
├── assembler.py        # Two-pass assembler
├── processor.py        # CPU simulation engine
├── gui.py              # tkinter GUI frontend
├── simulator.py        # Entry point
├── build_exe.py        # PyInstaller build script
├── examples/           # Built-in example programs
│   ├── fibonacci.asm
│   ├── multiply.asm
│   ├── divide.asm
│   ├── power.asm
│   ├── addressing_modes.asm
│   └── mano_style.asm
└── test_processor.py   # Unit tests
```

---

## Running

**From source** (requires Python 3.10+):
```bash
pip install tk
python simulator.py
```

**Build standalone EXE** (requires PyInstaller):
```bash
pip install pyinstaller
python build_exe.py
# Output: dist/16bit_Processor_Simulator.exe
```

---

## Course Info

- **Course:** CE-222 Computer Organization and Assembly Language (COAL)
- **Department:** Faculty of Computer Science and Engineering (FCSE)
- **University:** Ghulam Ishaq Khan Institute of Engineering Sciences and Technology (GIKI)