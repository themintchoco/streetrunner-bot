from enum import IntFlag


class Privacy(IntFlag):
    balance = 1 << 0
    prison = 1 << 1
    arena = 1 << 2
    time = 1 << 3
