        ORG  0          / Fibonacci Sequence: F(0) to F(4)
                        / Each term = sum of the two before it
                        / Results: 0  1  1  2  3

        CLA             / F(0) = 0
        STA  F0
        LDA  ONE        / F(1) = 1
        STA  F1
        LDA  F0         / F(2) = F(0) + F(1) = 1
        ADD  F1
        STA  F2
        LDA  F1         / F(3) = F(1) + F(2) = 2
        ADD  F2
        STA  F3
        LDA  F2         / F(4) = F(2) + F(3) = 3
        ADD  F3
        STA  F4
        HLT

ONE,    DEC  1          / constant 1
        ORG  100        / results stored at 100..104
F0,     DEC  0
F1,     DEC  0
F2,     DEC  0
F3,     DEC  0
F4,     DEC  0
        END