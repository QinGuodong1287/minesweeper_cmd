import os
import json
import math
import sys
import readline

import tool_constants

print("Welcome to the localization configuration tool.")
print("Latest modified date: 2023/5/23.")
print()
print("Initializing tool ...")
readline.clear_history()
with open(os.path.join(tool_constants.lang_path, "lang.json")) as settings:
    supported_languages = json.load(settings)["support_languages"]
untranslated_text_dict = {lang: {} for lang in supported_languages}
untranslated_text_attr_list = [{}]
text_index = 1
with open(os.path.join(tool_constants.lang_path,
                       r"untranslated_text.json")) as log:
    untranslated_text_list = json.load(log)
for item in untranslated_text_list:
    untranslated_text_dict.setdefault(item["lang"], {})
    untranslated_text_dict[item["lang"]][item["text"]] = ""
    if item["text"] in untranslated_text_attr_list[0]:
        cur_text_index = untranslated_text_attr_list[0][item["text"]]
        (untranslated_text_attr_list[cur_text_index]
         ["untranslated_languages"].add(item["lang"]))
    else:
        untranslated_text_attr_list.append({
            "text": item["text"],
            "untranslated_languages": set((item["lang"],)),
            "translated_languages": set()})
        untranslated_text_attr_list[0][item["text"]] = text_index
        text_index += 1
del untranslated_text_list
for lang in supported_languages:
    lang_file = os.path.join(tool_constants.lang_path, "{lang}.json".format(
        lang=lang))
    if not os.path.exists(lang_file):
        continue
    untranslated_text_dict.setdefault(lang, {})
    with open(lang_file) as file:
        translated_text_dict = json.load(file)
    untranslated_text_dict[lang].update(translated_text_dict)
    for text in translated_text_dict.keys():
        if text in untranslated_text_attr_list[0]:
            cur_text_index = untranslated_text_attr_list[0][text]
            (untranslated_text_attr_list[cur_text_index]
             ["untranslated_languages"].discard(lang))
            (untranslated_text_attr_list[cur_text_index]
             ["translated_languages"].add(lang))
        else:
            untranslated_text_attr_list.append({
                "text": text,
                "untranslated_languages": set(),
                "translated_languages": set((lang,))})
            untranslated_text_attr_list[0][text] = text_index
            text_index += 1
for lang in untranslated_text_dict.keys():
    for text in untranslated_text_attr_list[0].keys():
        if text in untranslated_text_dict[lang]:
            continue
        untranslated_text_dict[lang][text] = ""
        if text in untranslated_text_attr_list[0]:
            cur_text_index = untranslated_text_attr_list[0][text]
            (untranslated_text_attr_list[cur_text_index]
             ["untranslated_languages"].add(lang))
del text_index, cur_text_index


def askYesOrNo(prompt: str = "", default: bool | None = None,
               retry: bool = True) -> bool:
    prompt = str(prompt)
    if prompt:
        if "(y/n)" not in prompt.lower():
            choice = "({yes}/{no})".format(
                yes='Y' if default is True else 'y',
                no='N' if default is False else 'n')
            prompt = ' '.join((prompt, choice, ''))
    else:
        prompt = "Please enter y or n: "
    while True:
        user_input = input(prompt).lower()
        if not user_input:
            if default is not None:
                res = bool(default)
                break
        elif user_input in ('y', 'n'):
            res = user_input == 'y'
            break
        print("Your input is invaild. Please enter y or n.",
              file=sys.stderr)
        if not retry:
            res = False
            break
    return res


running = True


def exitTool():
    global running
    running = False


def printTextTable():
    global untranslated_text_attr_list
    index_len = int(math.log10(len(untranslated_text_attr_list) - 1)) + 1
    print("===== The untranslated text table =====")
    for index in range(1, len(untranslated_text_attr_list)):
        item = untranslated_text_attr_list[index]
        print("{num}.{text}".format(num=str(index).rjust(index_len),
                                    text=repr(item["text"])))


def printLanguages():
    global supported_languages
    print("===== The supported languages list =====")
    for index, lang in enumerate(supported_languages, 1):
        print(f"{index}.{lang}")


def translateText():
    global untranslated_text_dict, untranslated_text_attr_list
    keep_lang = False
    while True:
        try:
            if not keep_lang:
                lang = input("Please enter the language: ")
                if lang not in untranslated_text_dict.keys():
                    raise ValueError
                keep_lang = askYesOrNo("Keep this language?")
            index = int(input("Please enter the number of the text: "))
            if not (1 <= index < len(untranslated_text_attr_list)):
                raise ValueError
        except ValueError:
            print("Your input is invaild. Translation is aborted.",
                  file=sys.stderr)
            break
        untranslated_text = untranslated_text_attr_list[index]["text"]
        print("The text is {}.".format(repr(untranslated_text)))
        translated_text = untranslated_text_dict[lang][untranslated_text]
        if translated_text.strip():
            print("A translated text is {}.".format(repr(translated_text)))
        try:
            translated_text = input("Please enter the translated text:\n")
        except KeyboardInterrupt:
            print("The translation is finished.")
            break
        translated_text = eval(repr(translated_text).replace('\\\\', '\\'))
        untranslated_text_dict[lang][untranslated_text] = translated_text
        if not askYesOrNo("Do you want to translate another text?"):
            break


def retainAllTexts():
    global untranslated_text_dict
    lang = input("Please enter the language: ")
    if lang not in untranslated_text_dict.keys():
        print("Your input is invaild. Translation is aborted.",
              file=sys.stderr)
        return
    if askYesOrNo("Retain all texts?"):
        for text in untranslated_text_dict[lang].keys():
            untranslated_text_dict[lang][text] = text


tool_cases = [
    {
        "label": "Exit the tool.",
        "target": exitTool
    },
    {
        "label": "Print the text table.",
        "target": printTextTable
    },
    {
        "label": "Print supported languages.",
        "target": printLanguages
    },
    {
        "label": "Translate a text.",
        "target": translateText
    },
    {
        "label": "Retain all texts.",
        "target": retainAllTexts
    }
]
tool_cases_num = len(tool_cases)
while running:
    try:
        print()
        for index, case in enumerate(tool_cases):
            print("{index}.{label}".format(index=index, label=case["label"]))
        op = int(input())
        if not (0 <= op < tool_cases_num):
            raise ValueError
    except ValueError:
        print("Your choice is invaild. Please try again.", file=sys.stderr)
        continue
    print()
    tool_cases[op]["target"]()
if askYesOrNo("Save translation data?"):
    print("Saving translation data ...")
    for lang, lang_data in untranslated_text_dict.items():
        with open(
            os.path.join(tool_constants.lang_path,
                         "{lang}.json".format(lang=lang)),
                'w') as data:
            json.dump(lang_data, data, ensure_ascii=False, indent=4)
