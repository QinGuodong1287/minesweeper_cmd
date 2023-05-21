from math import log10
from functools import reduce
import os
import json


def uni_len(s: str):
    return reduce(lambda length, char: length + (
        2 if ord(char) not in range(128) else 1), s, 0)


def num_len(n: int) -> int:
    return int(log10(n)) + 1


def str_ljust(s: str, length: int) -> str:
    return ''.join((s, ' ' * (length - uni_len(s))))


def loadFile(file_path, default=None):
    if not os.path.exists(file_path):
        if default is None:
            return None
        with open(file_path, "w", encoding="utf-8") as fp:
            json.dump(default, fp, indent=4, ensure_ascii=False)
    with open(file_path, "r", encoding="utf-8") as fp:
        data = json.load(fp)
    return data


def saveFile(file_path, data):
    with open(file_path, "w", encoding="utf-8") as fp:
        json.dump(data, fp, indent=4, ensure_ascii=False)


def loadDict(file_path, d):
    new_d = loadFile(file_path, d)
    for key, value in new_d.items():
        d[key] = value
    return d
