from functools import reduce, partial
import os
import curses

from constants import settings_file
from basic_functions import uni_len, str_ljust, loadDict, saveFile
import graphics
import tutorial
import localize


class Settings(tutorial.GameTutorialMixin, graphics.Window):
    def __init__(self, parent):
        super().__init__(parent=parent)
        global settings
        self.settings = settings
        self.options = [
            {"name": localize.tr("键位设置"), "command": self.setKeyMap}
        ]
        self.max_name_len = max(self.options,
                                key=lambda option: uni_len(option["name"]))
        self.cur_index = 0
        self.options_len = len(self.options)
        self.default_key_notice = localize.tr(
            "按上下键切换所选设置，按Enter键打开所选设置，按“q”键退出设置。")
        self.reg_tutor("common", self.default_key_notice)

    def showPage(self, *geometries, key_notice=None, key_handler=None,
                 update=True, tutor=None):
        self.win.erase()
        terminal_size = os.get_terminal_size()
        self.win.addstr(0, 0, "游戏设置", curses.A_NORMAL)
        if key_notice is None:
            key_notice = self.default_key_notice
        else:
            key_notice = str(key_notice)
        self.win.addstr(1, 0, key_notice, curses.A_NORMAL)
        start_y = 1 + len(key_notice.splitlines())
        indent = 4
        # spaces = ' ' * indent

        def translate(item, keep_normal=False):
            if callable(item) and not keep_normal:
                res = item()
                if isinstance(res, dict):
                    if "text" in res:
                        res["text"] = str(res["text"])
                    else:
                        res["text"] = str(res)
                    if "attr" not in res:
                        res["attr"] = curses.A_NORMAL
                    return res
                else:
                    return {"text": str(res), "attr": curses.A_NORMAL}
            else:
                return {"text": str(item), "attr": curses.A_NORMAL}

        def getColumnWidth(geometry, depth=0):
            if isinstance(geometry, dict):
                new_width = width = indent * depth
                for label, subitem in geometry.items():
                    width = max(indent * depth + uni_len(translate(
                        label, not update)["text"]), new_width)
                    new_width = max(getColumnWidth(subitem, depth + 1), width)
                return new_width
            elif isinstance(geometry, (list, set, frozenset)):
                width = indent * depth
                for line in geometry:
                    width = max(getColumnWidth(line, depth), width)
                return width
            elif isinstance(geometry, tuple):
                return indent * depth + (uni_len(translate(
                    geometry[0], not update)["text"]) if geometry else 0)
            else:
                return indent * depth + uni_len(
                    translate(geometry, not update)["text"])
        cur_y = start_y

        def showGeometrySub(geometry, depth=0):
            nonlocal cur_y
            if isinstance(geometry, dict):
                for label, subitem in geometry.items():
                    data = translate(label, not update)
                    self.win.addstr(cur_y, indent * depth, data["text"],
                                    data["attr"])
                    cur_y += 1
                    showGeometrySub(subitem, depth + 1)
            elif isinstance(geometry, (list, set, frozenset)):
                for line in geometry:
                    showGeometrySub(line, depth)
            elif isinstance(geometry, tuple):
                data = (
                    translate(geometry[0], not update)
                    if geometry
                    else {"text": "", "attr": curses.A_NORMAL})
                self.win.addstr(cur_y, indent * depth, data["text"],
                                data["attr"])
                cur_x = label_width + 1
                for part in geometry[1:]:
                    data = translate(part, not update)
                    self.win.addstr(cur_y, cur_x, data["text"], data["attr"])
                    cur_x += uni_len(data["text"]) + 1
                cur_y += 1
            else:
                data = translate(geometry, not update)
                self.win.addstr(cur_y, indent * depth, data["text"],
                                data["attr"])
                line_num = len(data["text"].splitlines())
                cur_y += max(line_num, 1)
        for geometry in geometries:
            label_width = getColumnWidth(geometry)
            showGeometrySub(geometry)
        if tutor is not None:
            self.switch_tutor(str(tutor))
        if key_handler is not None:
            key = self.win.getch(terminal_size.lines - 1,
                                 terminal_size.columns - 1)
            if callable(key_handler):
                key_handler(key)

    def eventloop(self):
        def keyHandler(key):
            if key == ord('q'):
                self.close()
                return
            if key == curses.KEY_UP:
                self.cur_index = (self.cur_index - 1) % self.options_len
            elif key == curses.KEY_DOWN:
                self.cur_index = (self.cur_index + 1) % self.options_len
            elif key == ord('\n'):
                self.options[self.cur_index]["command"]()
        page = [""]
        name_len = reduce(
            lambda length, option: max(uni_len(option["name"]), length),
            self.options, 0)
        for index, option in enumerate(self.options):
            page.append(partial(
                lambda index, option: {
                    "text": str_ljust(option["name"], name_len),
                    "attr": (curses.A_REVERSE
                             if index == self.cur_index
                             else curses.A_NORMAL)}, index, option))
        self.showPage(page, key_handler=keyHandler, tutor="common")

    def close(self):
        save_settings(self.settings)
        super().close()

    def handleException(self, exc):
        save_settings(self.settings)
        return super().handleException(exc)

    key_table = {
        curses.KEY_UP: localize.tr("上方向键"),
        curses.KEY_DOWN: localize.tr("下方向键"),
        curses.KEY_LEFT: localize.tr("左方向键"),
        curses.KEY_RIGHT: localize.tr("右方向键")
    }

    def setKeyMap(self):
        keymap = self.settings["keymap"]
        keyset = keymap["keyset"]
        keyset_num = len(keyset)

        def bindFunc(*items):
            nonlocal keymap, keyset
            key = eval("keyset[keymap[\"current_keyset\"]][\"key\"][{}]"
                       .format("][".join(repr(item) for item in items)))
            return "{}".format(Settings.key_table.get(key, chr(key)))

        def bind(*items):
            return partial(bindFunc, *items)
        key_notice = localize.tr("按左右方向键切换所选方案，按“q”键返回上一级设置。")
        titles = []
        for index, keys in enumerate(keyset):
            titles.append(partial(
                lambda index, keys: {"text": keys["name"],
                                     "attr": (
                                        curses.A_REVERSE
                                        if index == keymap["current_keyset"]
                                        else curses.A_NORMAL)}, index, keys))
        titles = tuple(titles)
        page = []
        page.append({
            localize.tr("移动"): [
                (localize.tr("上"), bind("move", "up")),
                (localize.tr("下"), bind("move", "down")),
                (localize.tr("左"), bind("move", "left")),
                (localize.tr("右"), bind("move", "right"))
            ],
            localize.tr("操作"): [
                (localize.tr("翻开格子"), bind("action", "check")),
                (localize.tr("标记格子（插旗）"), bind("action", "flag")),
                (localize.tr("翻开3x3范围内格子"), bind("action", "detect"))
            ],
            localize.tr("游戏流程"): [
                (localize.tr("退出游戏"), bind("game", "quit")),
                (localize.tr("暂停游戏"), bind("game", "pause")),
                (localize.tr("保存游戏"), bind("game", "save")),
                (localize.tr("打开游戏设置"), bind("game", "settings"))
            ]
        })
        self.reg_tutor(
            "set_key_map",
            localize.tr("按左右方向键切换按键方案，\n按“q”键保存所选键位方案并退出键位设置。\n请记住所选键位方案。"))
        keep = True

        def keyHandler(key):
            nonlocal keep
            if key == ord('q'):
                keep = False
                return
            if key == curses.KEY_LEFT:
                keymap["current_keyset"] = max(keymap["current_keyset"] - 1, 0)
            elif key == curses.KEY_RIGHT:
                keymap["current_keyset"] = min(keymap["current_keyset"] + 1,
                                               keyset_num - 1)
        while keep:
            self.showPage(titles, page, key_notice=key_notice,
                          key_handler=keyHandler, tutor="set_key_map")


def load_settings(settings):
    loadDict(settings_file, settings)


def save_settings(settings):
    saveFile(settings_file, settings)


settings = {}
load_settings(settings)
if "keymap" not in settings:
    settings["keymap"] = {"default": {}, "keyset": [], "current_keyset": 0}
keyset = settings["keymap"]["keyset"]
index = 0
for ks in keyset[:]:
    if ks["name"] in ("默认方案1", "默认方案2", "默认方案3"):
        del keyset[index]
    else:
        index += 1
del index
settings["keymap"]["default"] = {
    "move": {
        "up": curses.KEY_UP,
        "down": curses.KEY_DOWN,
        "left": curses.KEY_LEFT,
        "right": curses.KEY_RIGHT
    },
    "action": {
        "check": ord('c'),
        "flag": ord('f'),
        "detect": ord('t')
    },
    "game": {
        "quit": ord('q'),
        "pause": ord('p'),
        "save": ord('x'),
        "settings": ord('z')
    }
}
keyset.insert(0, {"name": "默认方案1", "key": settings["keymap"]["default"]})
keyset.insert(1, {"name": "默认方案2", "key": {
    "move": {
        "up": ord('w'),
        "down": ord('s'),
        "left": ord('a'),
        "right": ord('d')
    },
    "action": {
        "check": ord('c'),
        "flag": ord('f'),
        "detect": ord('t')
    },
    "game": {
        "quit": ord('q'),
        "pause": ord('p'),
        "save": ord('x'),
        "settings": ord('z')
    }
}})
keyset.insert(2, {"name": "默认方案3", "key": {
    "move": {
        "up": ord('i'),
        "down": ord('k'),
        "left": ord('j'),
        "right": ord('l')
    },
    "action": {
        "check": ord('c'),
        "flag": ord('f'),
        "detect": ord('t')
    },
    "game": {
        "quit": ord('q'),
        "pause": ord('p'),
        "save": ord('x'),
        "settings": ord('z')
    }
}})
try:
    if not (0 <= settings["keymap"]["current_keyset"] < len(keyset)):
        raise TypeError
except TypeError:
    settings["keymap"]["current_keyset"] = 0


def check_keymap(index, *names):
    global settings, keyset
    item = eval("keyset[index][\"key\"]{}".format(("[{}]".format(
        "][".join(repr(name) for name in names))) if names else ''))
    default_item = eval("settings[\"keymap\"][\"default\"]{}".format((
        "[{}]".format("][".join(repr(name) for name in names)))
        if names else ''))
    keys = set(item.keys())
    default_keys = default_item.keys()
    keys.update(default_keys)
    for key in keys:
        if key not in default_keys:
            continue
        if key not in item:
            item[key] = default_item[key]
            continue
        if isinstance(item[key], dict):
            new_names = tuple(list(names) + [key])
            check_keymap(index, *new_names)


for index in range(len(keyset)):
    check_keymap(index)
del keyset, index
save_settings(settings)
