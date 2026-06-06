        ORG  0          / Addressing Modes Demo
                        / Two modes from Mano Textbook

/ DIRECT: instruction holds the address; CPU reads M[addr]
        LDA  DATA       / AC = M[DATA] = 25
        STA  DRES       / M[DRES] = AC

/ INDIRECT: instruction holds a pointer; CPU reads M[M[ptr]]
        LDA  I  PTR     / AC = M[M[PTR]] = M[TVAL] = 99
        STA  IRES       / M[IRES] = AC

        HLT

DATA,   DEC  25         / direct operand value  (addr 5)
DRES,   DEC  0          / direct result         (addr 6)
PTR,    DEC  8          / pointer -> TVAL at address 8
TVAL,   DEC  99         / indirect target value (addr 8)
IRES,   DEC  0          / indirect result       (addr 9)
        END