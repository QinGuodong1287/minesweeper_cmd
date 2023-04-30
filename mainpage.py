import os
import curses
import math
from time import time

from constants import __version__, map_file
from basic_functions import uni_len, num_len, str_ljust
import graphics
from gamemap import MainGameMap, clearmap
from record import RecordPage
from settings import Settings
from about import AboutGame
from tutorial import GameTutorialPage
import tutorial

class Minesweeper(tutorial.GameTutorialMixin, graphics.Window):
    def __init__(self):
        super().__init__()
        self.welcome_msg = """欢迎来到扫雷。
按上下方向键选择操作，按Enter键执行所选操作。"""
        self.options = []
        self.cur_index = 0
        self.reset_options()
        self.reg_tutor("welcome", self.welcome_msg)

    def reset_options(self):
        self.options.clear()
        self.options.append({"name": "开始新游戏", "command": lambda: self.main_game(False)})
        if os.path.exists(map_file):
            self.options.append({"name": "继续游戏", "command": self.main_game})
        self.options.append({"name": "打开游戏设置", "command": self.show_settings})
        self.options.append({"name": "查看排行榜", "command": self.show_record})
        self.options.append({"name": "打开游戏教程", "command": self.show_tutorial, "active": True})
        self.options.append({"name": "关于游戏", "command": self.about_game})
        self.options.append({"name": "退出游戏", "command": self.close})

    def eventloop(self):
        self.reset_options()
        self.win.erase()
        terminal_size = os.get_terminal_size()
        self.win.addstr(terminal_size.lines - 1, 0, __version__, curses.A_NORMAL)
        welcome_msg_lines = list(self.welcome_msg.splitlines())
        option_len = len(self.options)
        start_y = (terminal_size.lines - option_len - len(welcome_msg_lines)) // 2
        for line_num, line in enumerate(welcome_msg_lines):
            self.win.addstr(start_y + line_num, (terminal_size.columns - uni_len(line)) // 2, line, curses.A_NORMAL)
        option_name_len = max([uni_len(option["name"]) for option in self.options]) + num_len(option_len) + 1
        left_x = (terminal_size.columns - option_name_len) // 2
        for index, option in enumerate(self.options):
            self.win.addstr(start_y + len(welcome_msg_lines) + index, left_x, str_ljust("{}.{}".format(index + 1, option["name"]), option_name_len), curses.A_REVERSE if index == self.cur_index else (curses.A_NORMAL if option.get("active", True) else curses.A_DIM))
        self.switch_tutor("welcome")
        self.refresh()
        key = self.win.getch(terminal_size.lines - 1, terminal_size.columns - 1)
        if key == curses.KEY_UP:
            self.cur_index = (self.cur_index - 1) % option_len
            if not self.options[self.cur_index].get("active", True):
                self.cur_index -= 1
        elif key == curses.KEY_DOWN:
            self.cur_index = (self.cur_index + 1) % option_len
            if not self.options[self.cur_index].get("active", True):
                self.cur_index += 1
        elif key == ord('\n'):
            self.options[self.cur_index]["command"]()

    def main_game(self, recover=True):
        if not recover:
            clearmap()
        if tutorial.tutor_active:
            initial = InitialSettings(self)
            initial.doModel()
            del initial
        game = MainGameMap(self)
        game.doModel()
        del game

    def show_settings(self):
        settings = Settings(self)
        settings.doModel()
        del settings

    def show_record(self):
        page = RecordPage(self)
        page.doModel()
        del page

    def about_game(self):
        about = AboutGame(self)
        about.doModel()
        del about

    def show_tutorial(self):
        tutor = GameTutorialPage(self)
        tutor.doModel()
        del tutor

class InitialSettings(graphics.Window):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.bad_time = 0
        self.win.nodelay(True)
        
    def eventloop(self):
        keyset_prompt = """为了更好地畅玩扫雷，建议你查看键位设置。
是否现在打开键位设置？(y/n)""".splitlines()
        keyset_bad_msg = "你的选择错误。请按“y”或“n”。"
        start_y = (self.terminal_size.lines - len(keyset_prompt) - 1) // 2
        for line_num, line in enumerate(keyset_prompt):
            self.win.addstr(start_y + line_num, (self.terminal_size.columns - uni_len(line)) // 2, line, curses.A_NORMAL)
        self.win.refresh()
        curses.echo()
        key = -1
        while True:
            if time() - self.bad_time > 3:
                self.win.addstr(start_y + len(keyset_prompt), (self.terminal_size.columns - uni_len(keyset_bad_msg)) // 2, ' ' * uni_len(keyset_bad_msg), curses.A_NORMAL)
            key = self.win.getch(start_y + len(keyset_prompt) - 1, (self.terminal_size.columns - uni_len(keyset_prompt[-1])) // 2 + uni_len(keyset_prompt[-1]))
            if key in (ord('y'), ord('n')):
                break
            if key > -1:
                self.win.addstr(start_y + len(keyset_prompt), (self.terminal_size.columns - uni_len(keyset_bad_msg)) // 2, keyset_bad_msg, curses.A_NORMAL)
                self.bad_time = time()
        curses.noecho()
        if key == ord('y'):
            keyset_settings = Settings(self)
            keyset_settings.setKeyMap()
            del keyset_settings
        self.close()

    def close(self):
        self.win.nodelay(False)
        super().close()
