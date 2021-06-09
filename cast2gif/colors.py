from enum import Enum
from cast2gif.types import numeric_enum


@numeric_enum
class CGAColor(Enum):
    BLACK = 0
    BLUE = 1
    GREEN = 2
    CYAN = 3
    RED = 4
    MAGENTA = 5
    BROWN = 6
    GRAY = 7

    DARK_GRAY = 8
    LIGHT_BLUE = 9
    LIGHT_GREEN = 10
    LIGHT_CYAN = 11
    LIGHT_RED = 12
    LIGHT_MAGENTA = 13
    YELLOW = 14
    WHITE = 15


def to_rgb(color):
    value = color.value & 0b1111  # Strip out the high attribute bits
    if value == int(CGAColor.BLACK):
        return 0, 0, 0
    elif value == int(CGAColor.BLUE):
        return 0, 0, 255
    elif value == int(CGAColor.GREEN):
        return 0, 255, 0
    elif value == int(CGAColor.CYAN):
        return 0, 255, 255
    elif value == int(CGAColor.RED):
        return 255, 0, 0
    elif value == int(CGAColor.MAGENTA):
        return 0xAA, 0x00, 0xAA
    elif value == int(CGAColor.BROWN):
        return 0xAA, 0x55, 0x00
    elif value == int(CGAColor.GRAY):
        return (0xAA,) * 3
    elif value == int(CGAColor.DARK_GRAY):
        return (0x55,) * 3
    elif value == int(CGAColor.LIGHT_BLUE):
        return 0x55, 0x55, 0xFF
    elif value == int(CGAColor.LIGHT_GREEN):
        return 0x55, 0xFF, 0x55
    elif value == int(CGAColor.LIGHT_CYAN):
        return 0x55, 0xFF, 0xFF
    elif value == int(CGAColor.LIGHT_RED):
        return 0xFF, 0x55, 0x55
    elif value == int(CGAColor.LIGHT_MAGENTA):
        return 0xFF, 0x55, 0xFF
    elif value == int(CGAColor.YELLOW):
        return 0xFF, 0xFF, 0x55
    elif value == int(CGAColor.WHITE):
        return 255, 255, 255
    else:
        raise Exception(f"Unsupported Color: {color} (value = {color.value})")


def ansi_to_cga(index):
    """Converts ANSI X.364 to CGA"""
    index = index % 8
    return CGAColor([0, 4, 2, 6, 1, 5, 3, 7][index])


@numeric_enum
class CGAAttribute(Enum):
    PLAIN = 0
    INVERSE = 1
    INTENSE = 8
