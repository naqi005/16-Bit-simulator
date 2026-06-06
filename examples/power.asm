        ORG  0          / Power Demo: PWR
                        / Computes BASE ^ EXP = 2 ^ 8 = 256

        LDA  BASE       / AC = 2
        PWR  EXP        / AC = 2 ^ 8 = 256
        STA  RES        / store result
        HLT

BASE,   DEC  2          / base value
EXP,    DEC  8          / exponent
RES,    DEC  0          / result (256)
        END