import os
import traceback

from constants import error_file


def log(filename, data):
    mode = 'w'
    with open(filename, mode) as fp:
        fp.write(str(data))


def logError():
    mode = 'a' if os.path.exists(error_file) else 'w'
    with open(error_file, mode) as fp:
        if mode != 'w':
            fp.write('\n')
        traceback.print_exc(file=fp)
