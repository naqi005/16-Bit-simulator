        ORG  100        / Start at address 100 (decimal)
        LDA  SUB        / Load subtrahend into AC
        CMA             / Complement AC
        INC             / Increment AC (negate: 2's complement)
        ADD  MIN        / Add minuend to AC
        STA  DIF        / Store result in DIF
        HLT             / Halt
MIN,    DEC  5          / Minuend = 5
SUB,    DEC  3          / Subtrahend = 3
DIF,    HEX  0          / Difference (result stored here)
        END