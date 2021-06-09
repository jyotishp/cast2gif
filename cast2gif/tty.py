from enum import Enum

from cast2gif.colors import CGAColor, CGAAttribute, ansi_to_cga
from cast2gif.types import to_int


def constrain(n, n_min, n_max):
    """Constrain n to the range [n_min, n_max)"""
    return min(max(n, n_min), n_max - 1)


class Screen(object):
    def __init__(self, width, height):
        self.col = 0
        self.row = 0
        self.width = width
        self.height = height
        self.screen = None
        self.foreground = CGAColor.GRAY
        self.background = CGAColor.BLACK
        self.attr = CGAAttribute.PLAIN
        self.bell = False
        self.hide_cursor = False
        self.clear(2)

    def clear(self, screen_portion=0):
        """
        Clears a portion or all of the screen

        :param screen_portion: 0 (default) clears from cursor to end of screen; 1 clears from cursor to the beginning of the screen; and 2 clears the entire screen
        :return: returns nothing
        """
        if screen_portion == 1:
            # Clear from the beginning of the screen to the cursor
            self.screen[self.row] = [None] * (self.width - self.col + 1) + self.screen[
                self.row
            ][self.col + 1 :]
            self.screen = [[None] * self.width for i in range(self.row)] + self.screen[
                self.row :
            ]
        elif screen_portion == 2:
            # Clear the entire screen
            self.screen = [[None] * self.width for i in range(self.height)]
        else:
            # Clear from the cursor to the end of the screen
            self.screen[self.row] = self.screen[self.row][: self.col] + [None] * (
                self.width - self.col
            )
            self.screen = self.screen[: self.row + 1] + [
                [None] * self.width for i in range(self.height - self.row - 1)
            ]

    def erase_line(self, line_portion=0):
        """
        Clears a portion or all of the current line

        :param line_portion: 0 (default) clears from cursor to end of line; 1 clears from cursor to the beginning of the line; and 2 clears the entire line
        :return: returns nothing
        """
        if line_portion == 1:
            # Clear from the beginning of the line to the cursor
            self.screen[self.row] = [None] * (self.width - self.col + 1) + self.screen[
                self.row
            ][self.col + 1 :]
        elif line_portion == 2:
            # Clear the entire line
            self.screen[self.row] = [None] * self.width
        else:
            # Clear from the cursor to the end of the line
            self.screen[self.row] = self.screen[self.row][: self.col] + [None] * (
                self.width - self.col
            )

    def write(self, char, foreground=None, background=None, attr=None):
        if char is None:
            return
        elif char == "\n":
            self.col = 0
            self.row += 1
        elif char == "\r":
            self.col = 0
        elif char == "\b":
            # backspace
            if self.col > 0:
                self.screen[self.row] = (
                    self.screen[self.row][: self.col - 1]
                    + self.screen[self.row][self.col :]
                    + [None]
                )
                self.col -= 1
        elif ord(char) == 127:
            # delete
            self.screen[self.row] = (
                self.screen[self.row][: self.col]
                + self.screen[self.row][self.col + 1 :]
                + [None]
            )
        elif char == "\x07":
            self.bell = True
        else:
            if foreground is None:
                foreground = self.foreground
            if background is None:
                background = self.background
            if attr is None:
                attr = self.attr
            if 0 <= self.row < self.height and 0 <= self.col < self.width:
                self.screen[self.row][self.col] = (char, foreground, background, attr)
            self.col += 1
        if self.col >= self.width:
            self.col = 0
            self.row += 1
        if self.row >= self.height:
            extra_rows = self.row - self.height + 1
            self.screen = self.screen[extra_rows:] + [
                [None] * self.width for _ in range(extra_rows)
            ]
            self.row = self.height - 1

    def move_up(self, rows=1):
        self.row = constrain(self.row - rows, 0, self.height)

    def move_down(self, rows=1):
        self.row = constrain(self.row + rows, 0, self.height)

    def move_left(self, cols=1):
        self.col = constrain(self.col - cols, 0, self.width)

    def move_right(self, cols=1):
        self.col = constrain(self.col + cols, 0, self.width)

    def move_to(self, col=None, row=None):
        if col is not None:
            self.col = col
        if row is not None:
            self.row = row


class ANSITerminal(Screen):
    """A simple ANSI terminal emulator"""

    class TerminalState(Enum):
        OUTSIDE = 0
        ESC = 1
        ESCBKT = 2
        OSC = 3

    def __init__(self, width, height):
        super().__init__(width, height)
        self._state = ANSITerminal.TerminalState.OUTSIDE
        self._esc = None
        self._stored_pos = None
        self._last_char = None

    def write(self, char):
        if char is None or len(char) == 0 or char in "\x13\x14\x15\x26":
            pass
        elif len(char) > 1:
            for c in char:
                self.write(c)
        elif self._state == ANSITerminal.TerminalState.OUTSIDE:
            if ord(char) == 27:
                self._state = ANSITerminal.TerminalState.ESC
            else:
                super().write(char)
        elif self._state == ANSITerminal.TerminalState.ESC:
            self._write_esc(char)
        elif self._state == ANSITerminal.TerminalState.ESCBKT:
            self._write_escbkt(char)
        elif self._state == ANSITerminal.TerminalState.OSC:
            # an Operating System Command is terminated by the BEL character
            # or by ESC\
            if char == "\x07" or char == "\\" and ord(self._last_char) == 27:
                self._state = ANSITerminal.TerminalState.OUTSIDE
        self._last_char = char

    def _write_esc(self, char):
        if char == "]":
            self._state = ANSITerminal.TerminalState.OSC
        elif char == "[":
            self._state = ANSITerminal.TerminalState.ESCBKT
            self._esc = ""
        elif char in "\030\031":
            self._state = ANSITerminal.TerminalState.OUTSIDE
        else:
            raise Exception(
                "Escape sequence ESC \\x%x is not currently supported!" % ord(char)
            )

    def _write_escbkt(self, char):
        esc_value = to_int(self._esc, 1)
        matched = True
        if char == "A":
            self.move_up(esc_value)
        elif char in "Be":
            self.move_down(esc_value)
        elif char in "Ca":
            self.move_right(esc_value)
        elif char in "D":
            self.move_left(esc_value)
        elif char in "d`":
            self.move_to(0, esc_value - 1)
        elif char in "E`":
            self.move_down(esc_value)
            self.write("\r")
        elif char in "F`":
            self.move_up(esc_value)
            self.write("\r")
        elif char in "G`":
            self.move_to(esc_value - 1)
        elif char == "H":
            esc_value = self._esc.split(";")
            if len(esc_value) == 2:
                row, col = esc_value
            elif len(esc_value) == 1:
                row, col = esc_value[0], None
            else:
                row, col = None, None
            self.move_to(to_int(col, 1) - 1, to_int(row, 1) - 1)
        elif char == "J":
            esc_value = to_int(self._esc, 0)
            self.clear(esc_value)
            if esc_value == 2:
                self.move_to(0, 0)
        elif char == "K":
            esc_value = to_int(self._esc, 0)
            self.erase_line(esc_value)
        elif char == "h":
            if self._esc == "?2004":
                # we don't need to handle bracketed paste mode
                pass
            else:
                raise Exception("ESC[%sh escape is currently unsupported!" % self._esc)
        elif char == "l":
            if self._esc == "?2004":
                # we don't need to handle bracketed paste mode
                pass
            else:
                raise Exception("ESC[%sl escape is currently unsupported!" % self._esc)
        elif char == "m":
            self._write_esc_m()
        elif char == "s":
            self._stored_pos = (self.col, self.row)
        elif char == "u":
            if self._stored_pos is not None:
                self.move_to(*self._stored_pos)
        elif char in "STfinhl":
            raise Exception(
                "ESC[%s%s escape is currently unsupported!" % (self._esc, char)
            )
        else:
            matched = False
        if matched:
            self._state = ANSITerminal.TerminalState.OUTSIDE
        self._esc += char

    def _write_esc_m(self):
        for esc in map(to_int, self._esc.split(";")):
            if esc is None:
                continue
            elif esc == 0:
                self.foreground = CGAColor.GRAY
                self.background = CGAColor.BLACK
                self.attr = CGAAttribute.PLAIN
            elif esc == 1:
                self.foreground |= CGAAttribute.INTENSE
            elif esc in [2, 21, 22]:
                self.foreground |= ~CGAAttribute.INTENSE
            elif esc == 5:
                self.background |= CGAAttribute.INTENSE
            elif esc == 7:
                self.attr |= CGAAttribute.INVERSE
            elif esc == 25:
                self.background &= ~CGAAttribute.INTENSE
            elif esc == 27:
                self.attr &= ~CGAAttribute.INVERSE
            elif esc in range(30, 38):
                self.foreground = (
                    self.foreground & CGAAttribute.INTENSE
                ) | ansi_to_cga(esc - 30)
            elif esc in range(40, 48):
                self.background = (
                    self.background & CGAAttribute.INTENSE
                ) | ansi_to_cga(esc - 40)
            elif esc in range(90, 98):
                self.foreground = ansi_to_cga(esc - 82)
            elif esc in range(100, 108):
                self.foreground = ansi_to_cga(esc - 92)
