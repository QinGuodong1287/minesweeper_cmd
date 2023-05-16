import os
import curses

from constants import __version__
from basic_functions import uni_len
import graphics
import localize


class AboutGame(graphics.Window):
    def __init__(self, parent):
        super().__init__(parent=parent)
        curses_version = str(curses.version, "utf-8")
        ncurses_version = "{major}.{minor}-{patch}".format(
            major=curses.ncurses_version.major,
            minor=curses.ncurses_version.minor,
            patch=curses.ncurses_version.patch)
        self.text_lines = localize.tr("""\
关于 扫雷
作者：Qin Guodong <qinguodong07@qq.com>
版本 {version}
curses 版本：{curses_version}
ncurses 库版本：{ncurses_version}""").format(
            version=__version__,
            curses_version=curses_version,
            ncurses_version=ncurses_version).splitlines()
        self.terminal_size = os.get_terminal_size()

    def eventloop(self):
        terminal_size = os.get_terminal_size()
        if terminal_size != self.terminal_size:
            self.win.erase()
            self.terminal_size = terminal_size
        self.win.addstr(0, 0, localize.tr("关于"), curses.A_NORMAL)
        start_y = (terminal_size.lines - len(self.text_lines)) // 2
        for line_num, line in enumerate(self.text_lines):
            self.win.addstr(start_y + line_num,
                            (terminal_size.columns - uni_len(line)) // 2,
                            line, curses.A_NORMAL)
        self.win.addstr(terminal_size.lines - 1, 0,
                        localize.tr("按“q”键退出该页面。"),
                        curses.A_NORMAL)
        key = self.win.getch(terminal_size.lines - 1,
                             terminal_size.columns - 1)
        if key == ord('q'):
            self.close()
            return
