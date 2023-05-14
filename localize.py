import os
import glob

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
lang_index_file_basename = r"lang.json"
lang_index_file = os.path.join(lang_path, lang_index_file_basename)
basic_functions.loadDict(lang_index_file, localize_settings)
localize_settings.setdefault("lang", "zh-CN")
basic_functions.saveFile(lang_index_file, localize_settings)
language_list = [
    os.path.basename(filename).split('.')[:-1]
    for filename in glob.iglob(os.path.join(lang_path, "*.json"))
    if filename != lang_index_file_basename]
