        ORG  0          / Division Demo: DIV
                        / Computes NUM / DEN = 100 / 4 = 25

        LDA  NUM        / AC = 100
        DIV  DEN        / AC = 100 / 4 = 25
        STA  QUOT       / store quotient
        HLT

NUM,    DEC  100        / dividend
DEN,    DEC  4          / divisor
QUOT,   DEC  0          / result (25)
        END