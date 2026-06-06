        ORG  0          / Multiplication Demo: MUL
                        / Computes A * B = 6 * 7 = 42

        LDA  A          / AC = 6
        MUL  B          / AC = 6 * 7 = 42
        STA  RES        / store result
        HLT

A,      DEC  6          / first operand
B,      DEC  7          / second operand
RES,    DEC  0          / result (42)
        END