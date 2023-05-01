from math import log10
from functools import reduce
import os
import json

uni_len = lambda s: reduce(lambda length, char: length + (2 if ord(char) not in range(128) else 1), s, 0)
num_len = lambda n: int(log10(n)) + 1
str_ljust = lambda s, l: ''.join((s, ' ' * (l - uni_len(s))))


def loadFile(file_name, default=None):
    if not os.path.exists(file_name):
        if default is None:
            return None
        with open(file_name, "w") as fp:
            json.dump(default, fp, ensure_ascii=False)
    with open(file_name, "r") as fp:
        data = json.load(fp)
    return data


def saveFile(file_name, data):
    with open(file_name, "w") as fp:
        json.dump(data, fp, indent=4, ensure_ascii=False)


def loadDict(file_name, d):
    new_d = loadFile(file_name, d)
    for key, value in new_d.items():
        d[key] = value
