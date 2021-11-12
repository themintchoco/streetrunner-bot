from enum import IntFlag


class Privacy(IntFlag):
    balance = 1 << 0
    mines = 1 << 1
    arena = 1 << 2
    time = 1 << 3
