import curses

from .constants import settings_file
from .basic_functions import loadDict, saveFile


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
