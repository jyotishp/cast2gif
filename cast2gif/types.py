from enum import Enum


def numeric_enum(c):
    def __and__(self, n):
        if isinstance(n, Enum):
            n = n.value
        return EnumAwareInt(int(self.value) & int(n))

    def __or__(self, n):
        if isinstance(n, Enum):
            n = n.value
        return EnumAwareInt(int(self.value) | int(n))

    def __invert__(self):
        return EnumAwareInt(~int(self.value))

    def __int__(self):
        return self.value

    setattr(c, "__and__", __and__)
    setattr(c, "__or__", __or__)
    setattr(c, "__invert__", __invert__)
    setattr(c, "__int__", __int__)
    return c


@numeric_enum
class EnumAwareInt(object):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return f"EnumAwareInt({self.value!r})"


def to_int(n, default=None):
    try:
        return int(n)
    except (TypeError, ValueError):
        return default
