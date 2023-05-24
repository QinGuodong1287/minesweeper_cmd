import os
import atexit

from . import constants
from . import basic_functions

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


def initializeLocalizeSettings():
    global localize_settings, lang_index_file, lang_path
    default_lang = "zh-CN"
    localize_settings.setdefault("lang", default_lang)
    localize_settings["default_lang"] = default_lang
    localize_settings["support_languages"] = [
        "zh-CN",
        "en"]
    for lang in localize_settings["support_languages"]:
        lang_file = os.path.join(lang_path, "{lang}.json".format(lang=lang))
        if not os.path.exists(lang_file):
            basic_functions.saveFile(lang_file, {})
    localize_settings.setdefault("log_untranslated_text_flag", False)
    basic_functions.saveFile(lang_index_file, localize_settings)


initializeLocalizeSettings()


def current_language():
    global localize_settings
    return (
        localize_settings["lang"]
        if localize_settings["lang"] in localize_settings["support_languages"]
        else localize_settings["default_lang"])


language_data = {}
basic_functions.loadDict(os.path.join(lang_path, "{lang}.json".format(
    lang=current_language())), language_data)


def switchLanguage(new_lang: str):
    new_lang = str(new_lang)
    global localize_settings, language_data, lang_path
    localize_settings["lang"] = new_lang
    lang_file = os.path.join(lang_path, "{lang}.json".format(lang=new_lang))
    if os.path.exists(lang_file):
        language_data.clear()
        basic_functions.loadDict(lang_file, language_data)


def translate(source_text: str, dictionary: dict) -> str:
    if not isinstance(dictionary, dict):
        raise ValueError("The dictionary is not a dict.")
    source_text = str(source_text)
    global localize_settings
    return dictionary.get(localize_settings["lang"], source_text)


untranslated_text_log_file = os.path.join(lang_path, r"untranslated_text.json")
if os.path.exists(untranslated_text_log_file):
    untranslated_text_list = list(basic_functions.loadFile(
            untranslated_text_log_file))
else:
    untranslated_text_list = []


def tr(source_text: str) -> str:
    source_text = str(source_text)
    global localize_settings, language_data
    translated_text = language_data.get(source_text, '')
    if not translated_text.strip():
        if localize_settings["log_untranslated_text_flag"]:
            global untranslated_text_list
            text_data = {
                "text": source_text,
                "lang": localize_settings["lang"]}
            if text_data not in untranslated_text_list:
                untranslated_text_list.append(text_data)
        return source_text
    return translated_text


@atexit.register
def saveLocalizeData():
    global localize_settings, lang_index_file
    basic_functions.saveFile(lang_index_file, localize_settings)
    if localize_settings["log_untranslated_text_flag"]:
        global untranslated_text_set, untranslated_text_log_file
        basic_functions.saveFile(
            untranslated_text_log_file,
            untranslated_text_list)
