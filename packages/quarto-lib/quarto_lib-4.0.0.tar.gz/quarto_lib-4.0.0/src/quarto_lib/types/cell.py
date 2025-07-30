from enum import IntEnum


class Cell(IntEnum):
    A1 = 0b1100
    A2 = 0b1000
    A3 = 0b0100
    A4 = 0b0000
    B1 = 0b1101
    B2 = 0b1001
    B3 = 0b0101
    B4 = 0b0001
    C1 = 0b1110
    C2 = 0b1010
    C3 = 0b0110
    C4 = 0b0010
    D1 = 0b1111
    D2 = 0b1011
    D3 = 0b0111
    D4 = 0b0011

    @property
    def row(self) -> int:
        return self.value >> 2

    @property
    def col(self) -> int:
        return self.value & 0b11
