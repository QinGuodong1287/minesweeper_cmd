import os

import constants
import basic_functions

lang_path = os.path.join(constants.program_path, r"lang")
if not os.path.exists(lang_path):
    need_mkdir = True
elif not os.path.isdir(lang_path):
    os.unlink(lang_path)
    need_mkdir = True
else:
    need_mkdir = False
if need_mkdir:
    os.mkdir(lang_path)
del need_mkdir
localize_settings = {}
lang_index_file = os.path.join(lang_path, r"lang.json")
basic_functions.loadDict(lang_index_file, localize_settings)
localize_settings.setdefault("lang", "zh-CN")
basic_functions.saveFile(lang_index_file, localize_settings)
