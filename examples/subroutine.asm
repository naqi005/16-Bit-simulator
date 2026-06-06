        ORG  0          / BSA Subroutine Demo
                        / Calls ADD10: adds 10 to whatever is in AC

        LDA  VAL        / AC = 5
        BSA  ADD10      / call subroutine; return addr saved at ADD10
        STA  RES        / AC = 15; store result
        HLT

VAL,    DEC  5          / input value
RES,    DEC  0          / result (will be 15)

/ ADD10 subroutine: AC = AC + 10
/ BSA saves the return address into the first word (ADD10 slot)
/ then execution begins at ADD10+1
ADD10,  HEX  0          / return address slot (written by BSA)
        ADD  TEN        / AC = AC + 10
        BUN  I  ADD10   / return: branch indirect through slot

TEN,    DEC  10         / constant 10
        END