from functools import reduce
from time import time
import os
import curses

from . import loader
from core.basic_functions import uni_len
from core import graphics
from core import localize
from core.record import read_records


class RecordPage(graphics.Window):
    def __init__(self, parent, records=None):
        super().__init__(parent=parent)
        self.records = records if records is not None else {}
        if records is None:
            read_records(self.records)
        self.label_index = 0
        self.format_time = False
        self.win.nodelay(True)

        self.start_time = time()

    def eventloop(self):
        self.win.erase()
        terminal_size = os.get_terminal_size()
        self.win.addstr(0, 0, localize.tr("排行榜"), curses.A_NORMAL)
        self.win.addstr(1, 0, localize.tr("模式"), curses.A_NORMAL)
        label_len = max(reduce(lambda length, key: max(len(key), length),
                               self.records.keys(), 0), 4)
        for index, label in enumerate(self.records.keys()):
            self.win.addstr(1 + index + 1, 0, label.ljust(label_len),
                            curses.A_REVERSE
                            if index == self.label_index
                            else curses.A_NORMAL)
        page_columns = (
            localize.tr("名字"),
            localize.tr("用时"),
            localize.tr("记录时间"))
        self.win.addstr(1, label_len + 1, localize.tr("记录"), curses.A_NORMAL)
        self.win.addstr(2, label_len + 1, page_columns[0], curses.A_NORMAL)
        labels = list(self.records.keys())
        label = labels[self.label_index] if labels else ''
        name_len = reduce(
            lambda length, record: max(length, uni_len(record["name"])),
            self.records.get(label, []), 0)
        self.win.addstr(2, label_len + 1 + max(name_len, 4) + 1,
                        page_columns[1], curses.A_NORMAL)
        time_start_x = label_len + 1 + max(name_len, 4) + 1
        time_len = 4
        for index, record in enumerate(self.records.get(label, [])):
            self.win.addstr(2 + index + 1, label_len + 1, record["name"],
                            curses.A_NORMAL)
            if self.format_time:
                microseconds = int(record["time"] * 100)
                time_str = "{}:{}:{}.{}".format(
                    microseconds // 360000,
                    str(microseconds % 360000 // 6000).rjust(2, '0'),
                    str(microseconds % 6000 // 100).rjust(2, '0'),
                    str(microseconds % 100).rjust(2, '0'))
            else:
                time_str = str(record["time"]) + localize.tr("秒")
            time_len = max(uni_len(time_str), time_len)
            self.win.addstr(2 + index + 1,
                            label_len + 1 + max(name_len, 4) + 1, time_str,
                            curses.A_NORMAL)
        record_time_start_x = time_start_x + max(time_len, uni_len(
            page_columns[1])) + 1
        self.win.addstr(2, record_time_start_x, page_columns[2],
                        curses.A_NORMAL)
        for index, record in enumerate(self.records.get(label, [])):
            self.win.addstr(2 + index + 1, record_time_start_x,
                            record.get("record_time", ''), curses.A_NORMAL)
        key_notice = localize.tr(
            "按上下方向键切换要查看排行榜的模式，\n"
            "按“h”键切换用时显示方式，\n"
            "按“q”键退出排行榜。")
        key_notice_lines = key_notice.splitlines()
        wait_seconds = 3
        if time() - self.start_time > wait_seconds * len(key_notice_lines):
            self.start_time = time()
        index = (int((time() - self.start_time) / wait_seconds) %
                 len(key_notice_lines))
        self.win.addstr(
            terminal_size.lines - 1, 0,
            key_notice_lines[index],
            curses.A_NORMAL)
        self.refresh()
        key = self.win.getch(terminal_size.lines - 1,
                             terminal_size.columns - 1)
        if key == ord('q'):
            self.close()
            return
        if key == curses.KEY_UP:
            self.label_index = (self.label_index - 1) % len(labels)
        elif key == curses.KEY_DOWN:
            self.label_index = (self.label_index + 1) % len(labels)
        elif key == ord('h'):
            self.format_time = not self.format_time
