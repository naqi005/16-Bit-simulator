        ORG  0          / ALU Operations Demo
                        / ADD SUB MUL DIV MOD PWR AND OR XOR CMP
/ ADD: A + B = 35
        LDA  A          / AC = 15
        ADD  B          / AC = 15 + 20 = 35
        STA  RADD       / store result
/ SUB: C - D = 37
        LDA  C          / AC = 50
        SUB  D          / AC = 50 - 13 = 37
        STA  RSUB
/ MUL: E * F = 42
        LDA  E          / AC = 6
        MUL  F          / AC = 6 * 7 = 42
        STA  RMUL
/ DIV: G / H = 25
        LDA  G          / AC = 100
        DIV  H          / AC = 100 / 4 = 25
        STA  RDIV
/ MOD: J mod K = 2
        LDA  J          / AC = 17
        MOD  K          / AC = 17 mod 5 = 2
        STA  RMOD
/ PWR: L ^ M = 256
        LDA  L          / AC = 2
        PWR  M          / AC = 2 ^ 8 = 256
        STA  RPWR
/ AND: N AND P = 0x0F
        LDA  N          / AC = 0xFF
        AND  P          / AC = 0xFF AND 0x0F = 0x0F
        STA  RAND
/ OR: Q OR S = 0xFF
        LDA  Q          / AC = 0xF0
        OR   S          / AC = 0xF0 OR 0x0F = 0xFF
        STA  ROR
/ XOR: T XOR U = 0x55
        LDA  T          / AC = 0xFF
        XOR  U          / AC = 0xFF XOR 0xAA = 0x55
        STA  RXOR
/ CMP: compare V and W  ->  L=1 G=0 EQ=0
        LDA  V          / AC = 10
        CMP  W          / compare 10 with 20
        HLT
/ Input operands
A,      DEC  15         / ADD operand A
B,      DEC  20         / ADD operand B
C,      DEC  50         / SUB operand C
D,      DEC  13         / SUB operand D
E,      DEC  6          / MUL operand E
F,      DEC  7          / MUL operand F
G,      DEC  100        / DIV operand G
H,      DEC  4          / DIV operand H
J,      DEC  17         / MOD operand J
K,      DEC  5          / MOD operand K
L,      DEC  2          / PWR base
M,      DEC  8          / PWR exponent
N,      HEX  FF         / AND operand N
P,      HEX  0F         / AND operand P
Q,      HEX  F0         / OR operand Q
S,      HEX  0F         / OR operand S
T,      HEX  FF         / XOR operand T
U,      HEX  AA         / XOR operand U
V,      DEC  10         / CMP operand V
W,      DEC  20         / CMP operand W
        ORG  512        / Result storage
RADD,   DEC  0          / ADD result  (35)
RSUB,   DEC  0          / SUB result  (37)
RMUL,   DEC  0          / MUL result  (42)
RDIV,   DEC  0          / DIV result  (25)
RMOD,   DEC  0          / MOD result  ( 2)
RPWR,   DEC  0          / PWR result  (256)
RAND,   DEC  0          / AND result  (0x0F)
ROR,    DEC  0          / OR  result  (0xFF)
RXOR,   DEC  0          / XOR result  (0x55)
        END