from time import ctime

from .constants import records_file
from .basic_functions import loadDict, saveFile


def read_records(records):
    loadDict(records_file, records)


def store_record(records, width, height, max_mine_num, total_time,
                 name="Anonymous"):
    time_str = ctime()
    label = "{}x{}-{}".format(width, height, max_mine_num)
    if label not in records:
        records[label] = []
    name = name or "Anonymous"
    try:
        plain_name = str(name, "utf-8")
    except TypeError:
        plain_name = name
    records[label].append({"name": plain_name, "time": total_time,
                           "record_time": time_str})
    records[label].sort(key=lambda rec: rec["time"])
    del records[label][10:]


def save_records(records):
    saveFile(records_file, records)
