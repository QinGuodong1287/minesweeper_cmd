from math import inf
import os
import curses
from functools import reduce

from basic_functions import uni_len, str_ljust
import graphics

tutor_active = False

class GameTutorialMixin:
    title = "游戏教程"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tutor_table = {}
        self.init_tutor()

    def reg_tutor(self, name, text, x=inf, y=inf, attr=None):
        attr = int(attr) if attr else curses.A_NORMAL
        if name in self.tutor_table:
            self.tutor_table[name]["text"] = text
            self.tutor_table[name]["x"] = x
            self.tutor_table[name]["y"] = y
            self.tutor_table[name]["attr"] = attr
        else:
            self.tutor_table[name] = {"text": text, "x": x, "y": y, "attr": attr}

    def del_tutor(self, name):
        if name not in self.tutor_table:
            return
        del self.tutor_table[name]

    def switch_tutor(self, name, win=None):
        global tutor_active
        if not tutor_active:
            return
        win = win or self.win
        terminal_size = os.get_terminal_size()
        if name not in self.tutor_table:
            return
        tutor_item = self.tutor_table[name]
        text = tutor_item["text"]
        text_lines = str(text() if text and callable(text) else text).splitlines()
        text_max_line_len = max(reduce(lambda length, line: max(length, uni_len(line)), text_lines, 0), uni_len(GameTutorialMixin.title))
        start_y = min(tutor_item["y"], terminal_size.lines - len(text_lines) - 3)
        start_x = min(tutor_item["x"], terminal_size.columns - text_max_line_len - 3)
        win.addstr(start_y, start_x, '+' + '-' * text_max_line_len + '+', curses.A_NORMAL)
        win.addstr(start_y + 1, start_x, '|', curses.A_NORMAL)
        win.addstr(start_y + 1, start_x + 1, str_ljust(GameTutorialMixin.title, text_max_line_len), tutor_item["attr"])
        win.addstr(start_y + 1, start_x + 1 + text_max_line_len, '|', curses.A_NORMAL)
        for line_num, line in enumerate(text_lines, 1):
            win.addstr(start_y + 1 + line_num, start_x, '|', curses.A_NORMAL)
            win.addstr(start_y + 1 + line_num, start_x + 1, str_ljust(line, text_max_line_len), tutor_item["attr"])
            win.addstr(start_y + 1 + line_num, start_x + 1 + text_max_line_len, '|', curses.A_NORMAL)
        win.addstr(start_y + 2 + len(text_lines), start_x, '+' + '-' * text_max_line_len + '+', curses.A_NORMAL)

    # These methods can be overwrited in the subclass.
    def init_tutor(self):
        pass

class GameTutorialHelper(graphics.Widget):
    title = "游戏教程"

    def __init__(self, parent):
        super().__init__(parent=parent, ts=0)
        self.tutor_table = {}

    def reg_tutor(self, name, text, x=inf, y=inf, attr=curses.A_NORMAL):
        if name not in self.tutor_table:
            self.tutor_table[name] = {}
        self.tutor_table[name]["text"] = text

class GameTutorialPage(graphics.Window):
    def __init__(self, parent):
        super().__init__(parent=parent)

    def eventloop(self):
        global tutor_active
        self.win.addstr(0, 0, "游戏教程", curses.A_NORMAL)
        self.win.addstr(1, 0, "欢迎来到扫雷游戏教程。按Enter键进入教程，按“q”键退出教程。", curses.A_NORMAL)
        key = self.win.getch(self.terminal_size.lines - 1, self.terminal_size.columns - 1)
        if key == ord('q'):
            tutor_active = False
            self.close()
            return
        if key != ord('\n'):
            return
        tutor_active = True
        self.close()
