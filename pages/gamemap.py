import math
import os
from functools import partial, reduce
from random import randrange
from time import time
import curses

from . import loader
from core.constants import map_file
from core.basic_data_type import LimitedVar
from core.basic_functions import (uni_len, num_len, str_ljust, loadFile,
                                  saveFile)
from core import graphics
from core import settings
from core.record import read_records, store_record, save_records
from core import localize
from . import tutorial


class Block:
    def __init__(self, symbol, name="", color_pair=graphics.WHITE):
        self.symbol = symbol
        self.name = name
        self.color_pair = color_pair

    def __str__(self):
        return str(self.symbol)

    def __eq__(self, other):
        return self.symbol == other.symbol

    def __ne__(self, other):
        return self.symbol != other.symbol


SYMBOL = {}
SYMBOL["cover"] = COVER = Block('#', "cover")
SYMBOL["blank"] = BLANK = Block(' ', "blank")
SYMBOL["mine"] = MINE = Block('*', "mine")
SYMBOL["flag"] = FLAG = Block('F', "flag", color_pair=graphics.RED)
SYMBOL["flagged_mine"] = FLAGGED_MINE = Block('*', "flagged_mine",
                                              color_pair=graphics.RED)
NUMBER = [Block(str(num), "number_{}".format(num)) for num in range(10)]
for symbol in NUMBER:
    SYMBOL[symbol.name] = symbol


class MainGameMap(tutorial.GameTutorialMixin, graphics.Window):
    default_maps = {
        "easy": {
            "width": 8,
            "height": 8,
            "max_mine_num": 10
        },
        "standard": {
            "width": 9,
            "height": 9,
            "max_mine_num": 10
        },
        "medium": {
            "width": 16,
            "height": 16,
            "max_mine_num": 32
        },
        "hard": {
            "width": 30,
            "height": 16,
            "max_mine_num": 96
        }
    }

    def __init__(self, parent):
        global settings
        super().__init__(parent=parent)
        stat = {}
        loadmap(stat)
        self.width = LimitedVar(stat.get("width", 30), min_value=0,
                                max_value=100)
        self.height = LimitedVar(stat.get("height", 16), min_value=0,
                                 max_value=100)
        max_remain_blocks = self.width.max_value * self.height.max_value
        self.remain_blocks = LimitedVar(
            stat.get(
                "remain_blocks",
                self.width.get() * self.height.get()),
            min_value=0, max_value=max_remain_blocks)
        self.game_map = stat.get("game_map", [[
            COVER for j in range(self.width.get())] for i in range(
                self.height.get())])
        self.mine_map = stat.get("mine_map", [[
            BLANK for j in range(self.width.get())] for i in range(
                self.height.get())])
        self.max_mine_num = LimitedVar(
            stat.get("max_mine_num", 96),
            min_value=0, max_value=max_remain_blocks - 1)
        self.mine_num = LimitedVar(
            stat.get("mine_num", self.max_mine_num.get()),
            min_value=0, max_value=max_remain_blocks - 1)
        self.real_mine_num = LimitedVar(
            stat.get("real_mine_num", self.max_mine_num.get()),
            min_value=0, max_value=max_remain_blocks - 1)
        self.cur_pos = [0, 0]
        self.mine_pos = stat.get("mine_pos", [])
        self.blank_pos = stat.get("blank_pos", [])
        self.check_stack = []
        self.detect_pos_list = []
        self.detect_time = 0
        self.win_or_lose = False
        self.game_running = False
        self.game_paused = False
        self.game_finished = False
        self.game_saved = False
        self.keep_mode = False
        self.end_time = self.start_time = 0
        self.total_time = stat.get("total_time", 0)
        self.game_started = self.total_time > 0
        self.text_table = {
            "game_saved": localize.tr("游戏已保存。")}
        self.load_settings()
        self.records = {}
        read_records(self.records)
        self.reg_tutor(
            "select_mode",
            localize.tr("按上下方向键选择所玩模式，按空格键可锁定模式。\n"
                        "“自定义”模式可以自定义地图大小及雷数，\n"
                        "“锁定模式”选项决定在重新开始游戏时是否回到模式选择界面。"))
        self.reg_tutor(
            "select_custom_mode",
            localize.tr("请输入地图宽度、高度和雷数。\n"
                        "按Tab键切换输入项。\n"
                        "按Enter键确认输入的地图信息。\n"
                        "“锁定模式”选项决定在重新开始游戏时是否回到模式选择界面。"))
        self.reg_tutor(
            "symbols",
            localize.tr("地图符号：\n"
                        "        #：未翻开的格子。\n"
                        "     空格：已翻开的格子。\n"
                        "        *：雷。\n"
                        "数字(1-9)：格子周围3x3范围内其余8个格子中含有的雷数。\n"
                        "        F：插旗。"))
        self.reg_tutor(
            "settings_key",
            lambda: localize.tr("如果忘记键位或想切换键位方案，可按{}打开设置。").format(
                settings.Settings.key_table.get(
                    self.keyset["game"]["settings"], "“{}”键".format(chr(
                        self.keyset["game"]["settings"])))))
        self.tutor_labels = ("symbols", "settings_key")
        self.tutor_label_index = 0
        self.tutor_time = time()
        self.reset(not os.path.exists(map_file))

    def reset(self, force=True):
        if force:
            self.select_mode()
            if self.error:
                return
            self.win.erase()
            self.win.addstr(os.get_terminal_size().lines - 1, 0,
                            localize.tr("正在生成地图……"),
                            curses.A_NORMAL)
            self.win.refresh()
            self.gen_map()
            self.prepare_blank_pos()
            self.total_time = 0
        self.cur_pos[0] = min(max(self.cur_pos[0], 0), self.height.get() - 1)
        self.cur_pos[1] = min(max(self.cur_pos[1], 0), self.width.get() - 1)
        self.game_started = self.total_time > 0
        self.game_running = True
        self.game_paused = False
        self.game_finished = False
        self.game_saved = False
        self.end_time = self.start_time = 0
        self.load_settings()
        if self.game_started:
            self.record_time()
        self.win.erase()
        self.win.nodelay(True)
        curses.echo()

    def select_mode(self):
        if self.keep_mode:
            return
        mode_win = self.win.derwin(0, 0)
        mode_win.nodelay(False)
        mode_win.keypad(True)
        prompt = localize.tr("请按上下方向键选择模式，\n按空格键选择是否锁定该模式，\n按“q”键退出该界面"
                             ).splitlines()
        prompt_line_num = len(prompt)
        label_map = {"easy": localize.tr("简单"),
                     "standard": localize.tr("标准"),
                     "medium": localize.tr("中等"),
                     "hard": localize.tr("困难")}
        mode_labels = list(MainGameMap.default_maps.keys())
        mode_labels.append(localize.tr("自定义"))
        labels = []
        for label in mode_labels[:]:
            new_label = label_map.get(label, label)
            map_attr = MainGameMap.default_maps.get(label)
            map_attr_str = "{}x{}-{}".format(
                map_attr["width"],
                map_attr["height"],
                map_attr["max_mine_num"]) if map_attr else ""
            labels.append(
                "{}{}".format(
                    new_label,
                    " ({})".format(map_attr_str) if map_attr_str else ''))
        max_label_len = reduce(
            lambda length, label: max(uni_len(label), length), labels, 0)
        label_num = len(labels)
        keep_prompt = localize.tr("[{}]锁定模式")
        keep_prompt_line_num = len(keep_prompt.splitlines())
        cur_index = 0

        def set_custom_mode():
            nonlocal self, mode_win
            last_terminal_size = os.get_terminal_size()
            custom_win = mode_win.derwin(0, 0)
            curses.noecho()

            def show_cursor(x, y):
                nonlocal custom_win
                custom_win.addch(y, x, ' ', curses.A_REVERSE)

            custom_win.erase()
            item_names = ["width", "height", "max_mine_num"]
            items = {"width": 0, "height": 0, "max_mine_num": 0}
            item_lens = {"width": num_len(self.width.max_value),
                         "height": num_len(self.height.max_value),
                         "max_mine_num": num_len(self.max_mine_num.max_value)}
            item_max_values = {"width": self.width.max_value,
                               "height": self.height.max_value,
                               "max_mine_num": self.max_mine_num.max_value}
            title = localize.tr("请输入地图信息，\n"
                                "按Tab键切换输入项，\n"
                                "按Enter键确认输入信息，\n"
                                "按空格键选择是否锁定该模式，\n"
                                "按“q”键退出该页面。").splitlines()
            title_line_num = len(title)
            prompt = localize.tr("""\
地图宽度：[{width}](1-{max_width})
地图高度：[{height}](1-{max_height})
地图雷数：[{mine_num}](1-{max_mine_num})""")
            input_box_symbol = '['
            format_prompt = partial(lambda **kwargs: prompt.format(
                max_width=self.width.max_value,
                max_height=self.height.max_value,
                max_mine_num=self.max_mine_num.max_value, **kwargs))
            keep_mode_prompt = localize.tr("[{}]锁定模式")
            bad_msg = {"size_error": localize.tr("你的雷数超出地图大小。请重新输入。"),
                       "empty": localize.tr("请输入所有项。")}
            bad_time = 0
            item_count = len(items)
            item_index = 0
            custom_win.nodelay(True)
            msg = ''
            while True:
                terminal_size = os.get_terminal_size()
                if terminal_size != last_terminal_size:
                    custom_win.erase()
                    last_terminal_size = terminal_size
                prompt_lines = format_prompt(
                    width=(
                        str(items["width"]) if items["width"] > 0 else ' ')
                    .ljust(item_lens["width"] + 1),
                    height=(
                        str(items["height"]) if items["height"] > 0 else ' ')
                    .ljust(item_lens["height"] + 1),
                    mine_num=(
                        str(items["max_mine_num"])
                        if items["max_mine_num"] > 0 else ' ')
                    .ljust(item_lens["max_mine_num"] + 1)).splitlines()
                start_y = (terminal_size.lines - title_line_num -
                           len(prompt_lines) - 1) // 2
                for line_num, line in enumerate(title):
                    custom_win.addstr(
                        start_y + line_num,
                        (terminal_size.columns - uni_len(line)) // 2,
                        line, curses.A_NORMAL)
                max_line_len = reduce(
                    lambda length, line: max(uni_len(line), length),
                    prompt_lines, 0)
                item_start_y = start_y + title_line_num
                start_x = (terminal_size.columns - max_line_len) // 2
                for line_num, line in enumerate(prompt_lines):
                    custom_win.addstr(item_start_y + line_num, start_x,
                                      line, curses.A_NORMAL)
                keep_prompt = keep_mode_prompt.format(
                    'x' if self.keep_mode else ' ')
                custom_win.addstr(
                    item_start_y + item_count,
                    (terminal_size.columns - uni_len(keep_prompt)) // 2,
                    keep_prompt, curses.A_NORMAL)
                input_box_symbol_index = prompt_lines[item_index].index(
                    input_box_symbol)
                text_width = uni_len(
                    prompt_lines[item_index][:input_box_symbol_index]) + 1
                show_cursor(
                    start_x + text_width + (
                        num_len(items[item_names[item_index]])
                        if items[item_names[item_index]] > 0 else 0),
                    item_start_y + item_index)
                if time() - bad_time > 3:
                    custom_win.addstr(
                        item_start_y + item_count + 1,
                        (terminal_size.columns - uni_len(msg)) // 2,
                        ' ' * uni_len(msg), curses.A_NORMAL)
                self.switch_tutor("select_custom_mode", win=custom_win)
                custom_win.refresh()
                key = custom_win.getch(terminal_size.lines - 1,
                                       terminal_size.columns - 1)
                if key == ord('q'):
                    curses.echo()
                    return True
                elif key == ord('\n'):
                    if any([item <= 0 for item in items.values()]):
                        msg = bad_msg["empty"]
                    elif items["max_mine_num"] >= (items["width"] *
                                                   items["height"]):
                        msg = bad_msg["size_error"]
                    else:
                        msg = ''
                    if not msg:
                        break
                    custom_win.addstr(
                        item_start_y + item_count + 1,
                        (terminal_size.columns - uni_len(msg)) // 2,
                        msg, curses.A_NORMAL)
                    bad_time = time()
                if key == ord('\t'):
                    item_index = (item_index + 1) % item_count
                elif ord('0') <= key <= ord('9'):
                    item = items[item_names[item_index]]
                    item = 10 * item + (key - ord('0'))
                    items[item_names[item_index]] = min(
                        item, item_max_values[item_names[item_index]])
                elif key == graphics.KEY_BACKSPACE:
                    items[item_names[item_index]] //= 10
                elif key == ord(' '):
                    self.keep_mode = not self.keep_mode
            for item_name in item_names:
                items[item_name] = max(items[item_name], 1)
            self.width.set(items["width"])
            self.height.set(items["height"])
            self.max_mine_num.set(items["max_mine_num"])
            custom_win.nodelay(False)
            curses.echo()

        while True:
            terminal_size = os.get_terminal_size()
            start_y = (terminal_size.lines - prompt_line_num - label_num -
                       keep_prompt_line_num) // 2
            start_x = (terminal_size.columns - max_label_len) // 2
            mode_win.erase()
            for line_num, line in enumerate(prompt):
                mode_win.addstr(start_y + line_num, (terminal_size.columns -
                                uni_len(line)) // 2, line, curses.A_NORMAL)
            for index, label in enumerate(labels):
                mode_win.addstr(
                    start_y + prompt_line_num + index, start_x,
                    str_ljust(label, max_label_len),
                    curses.A_REVERSE if index == cur_index else curses.A_NORMAL
                    )
            plain_keep_prompt = keep_prompt.format(
                'x' if self.keep_mode else ' ')
            mode_win.addstr(
                start_y + prompt_line_num + label_num,
                (terminal_size.columns - uni_len(plain_keep_prompt)) // 2,
                plain_keep_prompt, curses.A_NORMAL)
            self.switch_tutor("select_mode", win=mode_win)
            mode_win.refresh()
            key = mode_win.getch(terminal_size.lines - 1,
                                 terminal_size.columns - 1)
            if key == ord('q'):
                self.error = True
                return
            if key == curses.KEY_UP:
                cur_index = (cur_index - 1) % label_num
            elif key == curses.KEY_DOWN:
                cur_index = (cur_index + 1) % label_num
            elif key == ord(' '):
                self.keep_mode = not self.keep_mode
            elif key == ord('\n'):
                if mode_labels[cur_index] in MainGameMap.default_maps:
                    map_attr = MainGameMap.default_maps[mode_labels[cur_index]]
                    self.width.set(map_attr["width"])
                    self.height.set(map_attr["height"])
                    self.max_mine_num.set(map_attr["max_mine_num"])
                    break
                else:
                    if not set_custom_mode():
                        break

        self.game_map.clear()
        self.mine_map.clear()
        for i in range(self.height.get()):
            self.game_map.append([])
            self.mine_map.append([])
            for j in range(self.width.get()):
                self.game_map[-1].append(COVER)
                self.mine_map[-1].append(BLANK)
        mode_win.erase()
        mode_win.refresh()

    def load_settings(self):
        self.settings = settings.settings
        keymap = settings.settings["keymap"]
        keyset = keymap["keyset"]
        self.keyset = keyset[keymap["current_keyset"]]["key"]

    def gen_map(self):
        self.check_stack.clear()
        self.mine_pos.clear()
        self.detect_pos_list.clear()
        self.detect_time = 0
        self.game_started = False
        self.game_running = True
        self.game_paused = False
        self.game_finished = False
        self.remain_blocks.set(self.width.get() * self.height.get())
        self.total_time = self.end_time = self.start_time = 0
        self.real_mine_num.set(self.max_mine_num.get())
        self.mine_num.set(self.max_mine_num.get())
        mine_num = self.max_mine_num.get()
        for row_num in range(self.height.get()):
            for col_num in range(self.width.get()):
                self.game_map[row_num][col_num] = COVER
                self.mine_map[row_num][col_num] = BLANK
        while mine_num > 0:
            row_num = randrange(self.height.get())
            col_num = randrange(self.width.get())
            if self.mine_map[row_num][col_num] == MINE:
                continue
            self.mine_map[row_num][col_num] = MINE
            self.mine_pos.append((row_num, col_num))
            mine_num -= 1
        neighbours = []
        for row_num in range(self.height.get()):
            for col_num in range(self.width.get()):
                neighbours.clear()
                if (row_num, col_num) in self.mine_pos:
                    continue
                if row_num > 0:
                    neighbours.extend(
                        [self.mine_map[row_num - 1][cn]
                         for cn in range(
                            max(col_num - 1, 0),
                            min(col_num + 2, self.width.get()))])
                if row_num < self.height.get() - 1:
                    neighbours.extend(
                        [self.mine_map[row_num + 1][cn]
                         for cn in range(
                            max(col_num - 1, 0),
                            min(col_num + 2, self.width.get()))])
                if col_num > 0:
                    neighbours.append(self.mine_map[row_num][col_num - 1])
                if col_num < self.width.get() - 1:
                    neighbours.append(self.mine_map[row_num][col_num + 1])
                mine_count = neighbours.count(MINE)
                if mine_count <= 0:
                    continue
                self.mine_map[row_num][col_num] = NUMBER[mine_count]
        neighbours.clear()

    def prepare_blank_pos(self):
        self.blank_pos.clear()

        def append_numbers(nrow, ncol):
            nonlocal first_list_index
            if self.mine_map[nrow][ncol] in NUMBER:
                self.blank_pos[first_list_index].append((nrow, ncol))

        class ProgressBar:
            def __init__(self, win, current, total):
                self.win = win
                self.total = total
                self.current = current
                self.light_len = 5
                self.light_speed = 5
                self.cur_light = 0
                self.pre_msg = localize.tr("生成地图中……")

            def show_progress(self):
                start_x = uni_len(self.pre_msg)
                start_y = os.get_terminal_size().lines - 1
                progress = "({current}/{total})".format(
                    current=str(self.current).rjust(num_len(self.total)),
                    total=self.total)
                bar_len = (os.get_terminal_size().columns - start_x
                           - len(progress) - 2)
                cur_len = int(self.current / self.total * bar_len)
                cur_light_extend = math.ceil(self.light_len / bar_len *
                                             self.total)
                self.win.addstr(start_y, 0, self.pre_msg.ljust(start_x),
                                curses.A_NORMAL)
                self.win.addstr(start_y, start_x, progress + '[',
                                curses.A_NORMAL)
                self.win.addstr(start_y, start_x + len(progress) + 1,
                                ' ' * cur_len, curses.A_REVERSE)
                self.win.addstr(
                    start_y,
                    start_x + len(progress) + 1 + int(max(self.cur_light, 0) /
                                                      self.total * bar_len),
                    ' ' * min(math.ceil(cur_len - self.cur_light / self.total *
                                        bar_len),
                              int(self.light_len + min(self.cur_light, 0) /
                                  self.total * bar_len)),
                    curses.color_pair(graphics.GREEN) | curses.A_REVERSE)
                self.win.addstr(start_y, os.get_terminal_size().columns - 2,
                                ']', curses.A_NORMAL)
                self.win.refresh()
                self.cur_light = ((self.cur_light + cur_light_extend +
                                  self.light_speed) % (self.current +
                                                       cur_light_extend +
                                                       self.light_speed)
                                  - cur_light_extend)

            def step(self):
                self.current = min(self.current + 1, self.total)
                self.show_progress()

        bar = ProgressBar(self.win, 0, self.width.get() * self.height.get())
        for row_num, row in enumerate(self.mine_map):
            for col_num, block in enumerate(row):
                bar.step()
                if block != BLANK:
                    continue
                create_new_list = True
                first_list_index = -1
                for list_index, pos_list in enumerate(self.blank_pos):
                    if row_num > 0 and (
                        self.mine_map[row_num - 1][col_num] == BLANK or
                            self.mine_map[row_num - 1][col_num] in NUMBER):
                        if (row_num - 1, col_num) in pos_list:
                            pos_list.append((row_num, col_num))
                            create_new_list = False
                            if first_list_index < 0:
                                first_list_index = list_index
                    if row_num < self.height.get() - 1 and (
                        self.mine_map[row_num + 1][col_num] == BLANK or
                            self.mine_map[row_num + 1][col_num] in NUMBER):
                        if (row_num + 1, col_num) in pos_list:
                            pos_list.append((row_num, col_num))
                            create_new_list = False
                            if first_list_index < 0:
                                first_list_index = list_index
                    if col_num > 0 and (
                        self.mine_map[row_num][col_num - 1] == BLANK or
                            self.mine_map[row_num][col_num - 1] in NUMBER):
                        if (row_num, col_num - 1) in pos_list:
                            pos_list.append((row_num, col_num))
                            create_new_list = False
                            if first_list_index < 0:
                                first_list_index = list_index
                    if col_num < self.width.get() - 1 and (
                        self.mine_map[row_num][col_num + 1] == BLANK or
                            self.mine_map[row_num][col_num + 1] in NUMBER):
                        if (row_num, col_num + 1) in pos_list:
                            pos_list.append((row_num, col_num))
                            create_new_list = False
                            if first_list_index < 0:
                                first_list_index = list_index
                if create_new_list:
                    self.blank_pos.append([(row_num, col_num)])
                self.block_foreach_3x3(append_numbers, row_num, col_num)
        old_pos_lists = self.blank_pos[:]
        self.blank_pos.clear()
        for pos_list in old_pos_lists:
            pos_set = set(pos_list)
            for index, new_pos_list in enumerate(self.blank_pos):
                new_pos_set = set(new_pos_list)
                if new_pos_set.isdisjoint(pos_set):
                    continue
                new_pos_set.update(pos_set)
                self.blank_pos[index] = list(new_pos_set)
                break
            else:
                self.blank_pos.append(list(pos_set))

    def show_map(self):
        terminal_size = os.get_terminal_size()
        if terminal_size != self.terminal_size:
            self.win.erase()
            self.terminal_size = terminal_size
        if time() - self.tutor_time > 3:
            if tutorial.tutor_active:
                self.win.erase()
            self.tutor_label_index = ((self.tutor_label_index + 1) %
                                      len(self.tutor_labels))
            self.tutor_time = time()
        row_num_len = num_len(self.height.get())
        col_num_len = num_len(self.width.get())
        sep = '|'
        '''
        self.notice = notice = """剩余雷数：{mine_num}
按方向键控制光标（高亮）（以下称光标所在格子为当前格子）。
按“c”键翻开当前格子，按“f”键在当前格子插旗。
若当前格子周围3x3区域中的其余8个格子的插旗数等于当前格子内数字，可按“t”键翻开此3x3区域中剩余未翻开且未插旗的格子。
按“p”键暂停游戏，按“q”键退出游戏，按“x”键保存游戏。""".format(mine_num=str(self.mine_num).ljust(num_len(self.max_mine_num)))
        '''
        self.notice = notice = localize.tr("""剩余雷数：{mine_num}，用时：{time_str}"""
                                           ).format(
            mine_num=str(self.mine_num.get()).ljust(
                num_len(self.max_mine_num.get())),
            time_str=self.get_time_str())
        map_rows, map_cols = min(terminal_size.lines - len(notice.splitlines())
                                 - 1 - 8, self.height.get()), min(
                (terminal_size.columns - row_num_len -
                 len(sep)) // (col_num_len + len(sep)),
                self.width.get())
        self.map_rows = map_rows
        start_row, start_col = (min(max(self.cur_pos[0] - map_rows // 2, 0),
                                    self.height.get() - map_rows),
                                min(max(self.cur_pos[1] - map_cols // 2, 0),
                                    self.width.get() - map_cols))
        self.win.addstr(0, row_num_len + len(sep), (' ' * len(sep)).join(
            str(col_num).rjust(col_num_len) for col_num in range(
                start_col + 1, start_col + 1 + map_cols)),
            curses.A_NORMAL)
        for row_num in range(start_row, start_row + map_rows):
            row = self.game_map[row_num]
            self.win.addstr(row_num - start_row + 1, 0, str(row_num + 1).rjust(
                row_num_len) + sep, curses.A_NORMAL)
            for col_num in range(start_col, start_col + map_cols):
                block = row[col_num]
                self.win.addstr(
                    row_num - start_row + 1,
                    (row_num_len + len(sep) + (col_num - start_col) *
                     (col_num_len + len(sep))),
                    str(block).rjust(col_num_len),
                    curses.color_pair(
                        (block.color_pair
                         if (row_num, col_num) not in self.detect_pos_list or
                         block == FLAG
                         else graphics.BLUE) +
                        (10 if row_num == self.cur_pos[0] and
                         col_num == self.cur_pos[1] else 0)))
                self.win.addstr(
                    row_num - start_row + 1,
                    (row_num_len + len(sep) + (col_num - start_col + 1) *
                     (col_num_len + len(sep)) - len(sep)),
                    '|', curses.A_NORMAL)
        for line_num, line in enumerate(notice.splitlines()):
            self.win.addstr(1 + map_rows + line_num, 0, line, curses.A_NORMAL)
        self.win.addstr(
            terminal_size.lines - 1, 0,
            ' '.join(str(num) for num in self.cur_pos)
                .ljust(row_num_len + 1 + col_num_len), curses.A_NORMAL)
        if time() - self.start_time >= 3:
            self.win.addstr(
                terminal_size.lines - 1,
                num_len(self.height.get()) + 1 + num_len(self.width.get()) + 1,
                ' ' * uni_len(self.text_table["game_saved"]), curses.A_NORMAL)
        self.switch_tutor(self.tutor_labels[self.tutor_label_index])
        self.refresh()
        if time() - self.detect_time > 0.5:
            self.detect_pos_list.clear()

    def get_time_str(self):
        cur_time = self.total_time
        if self.start_time > self.end_time:
            cur_time += time() - self.start_time
        cur_time = int(cur_time)
        hour, minute, second = (cur_time // 3600, cur_time % 3600 // 60,
                                cur_time % 60)
        return "{}: {}: {}".format(hour, str(minute).rjust(2, '0'),
                                   str(second).rjust(2, '0'))

    def handle_lost(self):
        self.record_time()
        self.win.nodelay(False)
        for pos in self.mine_pos:
            if self.game_map[pos[0]][pos[1]] == FLAG:
                self.game_map[pos[0]][pos[1]] = FLAGGED_MINE
            else:
                self.game_map[pos[0]][pos[1]] = MINE
        self.show_map()
        self.win_or_lose = False
        self.game_started = True
        self.game_running = False
        self.game_paused = False
        self.game_finished = True
        notice_line_num = len(self.notice.splitlines())
        self.win.addstr(1 + self.map_rows + 2 + notice_line_num, 0,
                        localize.tr("你输了。"),
                        curses.A_NORMAL)
        self.show_time()
        self.ask_for_new_game()

    def handle_win(self):
        self.record_time()
        self.win.nodelay(False)
        self.show_map()
        self.win_or_lose = True
        self.game_started = True
        self.game_running = False
        self.game_paused = False
        self.game_finished = True
        notice_line_num = len(self.notice.splitlines())
        start_y = 1 + self.map_rows + 2 + notice_line_num
        self.win.addstr(start_y, 0, localize.tr("你赢了！"), curses.A_NORMAL)
        self.show_time()
        prompt = localize.tr("请输入你的名字（默认为Anonymous）：")
        self.win.addstr(start_y + 2, 0, prompt, curses.A_NORMAL)
        name = self.win.getstr(start_y + 2, uni_len(prompt))
        store_record(self.records, self.width.get(), self.height.get(),
                     self.max_mine_num.get(), self.total_time, name)
        self.ask_for_new_game()

    def show_time(self):
        notice_line_num = len(self.notice.splitlines())
        self.win.addstr(1 + self.map_rows + 2 + notice_line_num + 1, 0,
                        localize.tr("你用时{}秒。").format(self.total_time),
                        curses.A_NORMAL)

    def ask_for_new_game(self):
        self.win.nodelay(False)
        start_y = 1 + self.map_rows + 1 + len(self.notice.splitlines()) + 4
        prompt = localize.tr("是否开启新游戏？(y/n)")
        bad_msg = localize.tr("你的选择错误。请按“y”或“n”。")
        self.win.addstr(start_y, 0, prompt, curses.A_NORMAL)
        while True:
            choice = self.win.getch(start_y, uni_len(prompt))
            if choice in (ord('y'), ord('n')):
                break
            self.win.addstr(start_y + 1, 0, bad_msg, curses.A_NORMAL)
        self.win.addstr(start_y, 0, ' ' * (uni_len(prompt) + 1),
                        curses.A_NORMAL)
        self.win.addstr(start_y + 1, 0, ' ' * uni_len(bad_msg),
                        curses.A_NORMAL)
        self.refresh()
        clearmap()
        if choice == ord('n'):
            self.close()
            return
        self.reset()

    def block_foreach_3x3(self, func, row_num=None, col_num=None):
        if not callable(func):
            raise ValueError("The func is not callable.")
        if row_num is None:
            row_num = self.cur_pos[0]
        if col_num is None:
            col_num = self.cur_pos[1]
        if row_num > 0:
            for cn in range(max(col_num - 1, 0), min(col_num + 2,
                                                     self.width.get())):
                func(row_num - 1, cn)
        if row_num < self.height.get() - 1:
            for cn in range(max(col_num - 1, 0), min(col_num + 2,
                                                     self.width.get())):
                func(row_num + 1, cn)
        if col_num > 0:
            func(row_num, col_num - 1)
        if col_num < self.width.get() - 1:
            func(row_num, col_num + 1)

    def check_pos(self, row_num=None, col_num=None):
        if row_num is None:
            row_num = self.cur_pos[0]
        if col_num is None:
            col_num = self.cur_pos[1]
        if not (0 <= row_num < self.height.get() and 0 <= col_num <
                self.width.get()):
            return
        if not self.game_started:
            self.game_started = True
            self.record_time()
        if self.game_finished:
            return
        if (row_num, col_num) in self.check_stack:
            return
        if self.game_map[row_num][col_num] == FLAG:
            return
        if (self.game_map[row_num][col_num] != COVER and
                self.game_map[row_num][col_num] not in NUMBER):
            return
        self.check_stack.append((row_num, col_num))
        if self.mine_map[row_num][col_num] == MINE:
            self.handle_lost()
            return
        if self.game_map[row_num][col_num] == COVER:
            self.game_map[row_num][col_num] = self.mine_map[row_num][col_num]
            self.remain_blocks.set(self.remain_blocks.get() - 1)
        if (self.remain_blocks.get() <= self.max_mine_num.get() or
                self.real_mine_num.get() <= 0):
            self.handle_win()
            return
        if self.game_map[row_num][col_num] == BLANK:
            """
            def check_avoid_mine(nrow, ncol):
                if self.mine_map[nrow][ncol] == MINE:
                    return
                self.check_pos(nrow, ncol)
            self.block_foreach_3x3(check_avoid_mine, row_num, col_num)
            """
            found = False
            for pos_list in self.blank_pos:
                if (row_num, col_num) in pos_list:
                    found = True
                    break
            if found:
                for pos in pos_list:
                    if (pos != (row_num, col_num) and
                            self.game_map[pos[0]][pos[1]] == COVER):
                        self.remain_blocks.set(self.remain_blocks.get() - 1)
                    self.game_map[pos[0]][pos[1]] = \
                        self.mine_map[pos[0]][pos[1]]
        del self.check_stack[-1]
        if (self.remain_blocks.get() <= self.max_mine_num.get() or
                self.real_mine_num.get() <= 0):
            self.handle_win()
            return

    def flag_pos(self, row_num=None, col_num=None):
        if row_num is None:
            row_num = self.cur_pos[0]
        if col_num is None:
            col_num = self.cur_pos[1]
        if not self.game_started:
            self.game_started = True
            self.record_time()
        if self.game_map[row_num][col_num] not in (COVER, FLAG):
            return
        bad_msg = localize.tr("你插旗太多了，电摇你！")
        if self.game_map[row_num][col_num] != FLAG:
            if self.mine_num.get() <= 0 and self.real_mine_num.get() > 0:
                self.win.addstr(
                    self.height.get() + 1 + len(self.notice.splitlines()),
                    0, bad_msg, curses.A_NORMAL)
                return
            self.game_map[row_num][col_num] = FLAG
            self.mine_num.set(self.mine_num.get() - 1)
            if self.mine_map[row_num][col_num] == MINE:
                self.real_mine_num.set(self.real_mine_num.get() - 1)
        else:
            self.game_map[row_num][col_num] = COVER
            self.mine_num.set(self.mine_num.get() + 1)
            if self.mine_map[row_num][col_num] == MINE:
                self.real_mine_num.set(self.real_mine_num.get() + 1)
            self.win.addstr(
                1 + self.map_rows + 1 + len(self.notice.splitlines()),
                0, ' ' * uni_len(bad_msg), curses.A_NORMAL)
        if self.mine_num.get() <= 0 and self.real_mine_num.get() <= 0:
            self.handle_win()

    def detect_pos(self, row_num=None, col_num=None):
        if row_num is None:
            row_num = self.cur_pos[0]
        if col_num is None:
            col_num = self.cur_pos[1]
        if not self.game_started:
            self.game_started = True
            self.record_time()
        if (self.game_map[row_num][col_num] != BLANK and
                self.game_map[row_num][col_num] not in NUMBER):
            return
        flag_count = 0
        need_check_pos = []
        detected_mine = False
        update_list = [row_num, col_num] == self.cur_pos
        if update_list:
            self.detect_pos_list.clear()
            self.detect_time = time()

        def check_mine(nrow, ncol):
            nonlocal flag_count, detected_mine, update_list
            if self.game_map[nrow][ncol] != FLAG:
                need_check_pos.append((nrow, ncol))
                if update_list:
                    self.detect_pos_list.append((nrow, ncol))
                detected_mine = (detected_mine or
                                 self.mine_map[nrow][ncol] == MINE)
            else:
                flag_count += 1
        self.block_foreach_3x3(check_mine)
        if update_list:
            self.detect_pos_list.append((row_num, col_num))
        if self.game_map[row_num][col_num] in NUMBER:
            if self.game_map[row_num][col_num] != NUMBER[flag_count]:
                return
            if detected_mine:
                def show_block(nrow, ncol):
                    if self.game_map[nrow][ncol] == FLAG:
                        return
                    self.game_map[nrow][ncol] = self.mine_map[nrow][ncol]
                self.block_foreach_3x3(show_block)
                self.handle_lost()
                return
        else:
            if update_list:
                self.detect_pos_list.clear()
        for pos in need_check_pos:
            self.check_pos(pos[0], pos[1])

    def pause_game(self):
        self.game_paused = not self.game_paused
        if self.game_started:
            self.record_time()
        pause_key = self.keyset["game"]["pause"]
        msg = localize.tr("游戏已暂停。按“{}”键以继续游戏。").format(
            settings.Settings.key_table.get(
                pause_key, chr(pause_key)))
        if self.game_paused:
            self.win.addstr(
                1 + self.map_rows + 1 + len(self.notice.splitlines()),
                0, msg, curses.A_NORMAL)
        else:
            self.win.addstr(
                1 + self.map_rows + 1 + len(self.notice.splitlines()),
                0, ' ' * uni_len(msg), curses.A_NORMAL)

    def record_time(self):
        if self.start_time <= self.end_time:
            self.start_time = time()
        else:
            self.end_time = time()
            self.total_time += self.end_time - self.start_time

    def save_map(self):
        savemap(self.game_map, self.mine_map, self.total_time,
                self.remain_blocks.get(), self.mine_num.get(),
                self.max_mine_num.get(), self.real_mine_num.get(),
                self.mine_pos, self.blank_pos)

    def get_key(self):
        terminal_size = os.get_terminal_size()
        key = self.win.getch(
            terminal_size.lines - 1,
            terminal_size.columns - 1)
        if key in range(128):
            key = ord(chr(key).lower())
        if key == self.keyset["game"]["quit"]:
            if not self.game_saved:
                clearmap()
            self.close()
            return False
        elif key == self.keyset["game"]["pause"]:
            self.pause_game()
        elif key == self.keyset["game"]["save"]:
            self.record_time()
            self.record_time()
            self.save_map()
            self.game_saved = True
            self.win.addstr(
                terminal_size.lines - 1,
                num_len(self.height.get()) + 1 + num_len(self.width.get()) + 1,
                self.text_table["game_saved"], curses.A_NORMAL)
        elif key == self.keyset["game"]["settings"]:
            if not self.game_paused:
                self.pause_game()
            settings_page = settings.Settings(self)
            settings_page.doModel()
            del settings_page
            self.load_settings()
            if self.game_paused:
                self.pause_game()
        if not self.game_running:
            return False
        if self.game_paused:
            return True
        if key == self.keyset["move"]["up"]:
            self.cur_pos[0] = max(self.cur_pos[0] - 1, 0)
        elif key == self.keyset["move"]["down"]:
            self.cur_pos[0] = min(self.cur_pos[0] + 1, self.height.get() - 1)
        if key == self.keyset["move"]["left"]:
            self.cur_pos[1] = max(self.cur_pos[1] - 1, 0)
        elif key == self.keyset["move"]["right"]:
            self.cur_pos[1] = min(self.cur_pos[1] + 1, self.width.get() - 1)
        if key == self.keyset["action"]["check"]:
            self.check_pos()
        elif key == self.keyset["action"]["flag"]:
            self.flag_pos()
        elif key == self.keyset["action"]["detect"]:
            self.detect_pos()
        return True

    def eventloop(self):
        self.show_map()
        if not self.get_key():
            return

    def close(self):
        self.win.nodelay(False)
        curses.echo()
        save_records(self.records)
        super().close()

    def handleException(self, exc):
        if not self.game_finished:
            self.record_time()
            savemap(self.game_map, self.mine_map, self.total_time,
                    self.remain_blocks.get(), self.mine_num.get(),
                    self.max_mine_num.get(), self.real_mine_num.get(),
                    self.mine_pos, self.blank_pos)
        return super().handleException(exc)


def savemap(game_map, mine_map, total_time, remain_blocks, mine_num,
            max_mine_num, real_mine_num, mine_pos, blank_pos):
    plain_game_map = []
    for row in game_map:
        plain_game_map.append([])
        for block in row:
            plain_game_map[-1].append(block.name)
    plain_mine_map = []
    for row in mine_map:
        plain_mine_map.append([])
        for block in row:
            plain_mine_map[-1].append(block.name)
    saveFile(map_file, {"width": len(game_map[0]), "height": len(game_map),
                        "game_map": plain_game_map, "mine_map": plain_mine_map,
                        "total_time": total_time,
                        "remain_blocks": remain_blocks, "mine_num": mine_num,
                        "max_mine_num": max_mine_num,
                        "real_mine_num": real_mine_num, "mine_pos": mine_pos,
                        "blank_pos": blank_pos})


def loadmap(stat):
    plain_stat = loadFile(map_file)
    if plain_stat is None:
        return
    stat["width"] = plain_stat["width"]
    stat["height"] = plain_stat["height"]
    stat["game_map"] = []
    for row in plain_stat["game_map"]:
        stat["game_map"].append([])
        for block in row:
            stat["game_map"][-1].append(SYMBOL[block])
    stat["mine_map"] = []
    for row in plain_stat["mine_map"]:
        stat["mine_map"].append([])
        for block in row:
            stat["mine_map"][-1].append(SYMBOL[block])
    stat["total_time"] = plain_stat["total_time"]
    stat["remain_blocks"] = plain_stat["remain_blocks"]
    stat["mine_num"] = plain_stat["mine_num"]
    stat["max_mine_num"] = plain_stat["max_mine_num"]
    stat["real_mine_num"] = plain_stat["real_mine_num"]
    stat["mine_pos"] = []
    for pos in plain_stat["mine_pos"]:
        stat["mine_pos"].append(tuple(pos))
    stat["blank_pos"] = []
    for pos in plain_stat["blank_pos"]:
        stat["blank_pos"].append(tuple(pos))


def clearmap():
    try:
        os.remove(map_file)
    except FileNotFoundError:
        pass
