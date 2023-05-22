import os
import json
import sys
import readline

import tool_constants

print("Initializing tool ...")
readline.clear_history()
with open(os.path.join(tool_constants.lang_path, "lang.json")) as settings:
    supported_languages = json.load(settings)["support_languages"]
untranslated_text_dict = {lang: {} for lang in supported_languages}
untranslated_text_set = set()
with open(os.path.join(tool_constants.lang_path,
                       r"untranslated_text.json")) as log:
    untranslated_text_list = json.load(log)
for item in untranslated_text_list:
    untranslated_text_dict.setdefault(item["lang"], {})
    untranslated_text_dict[item["lang"]][item["text"]] = ""
    untranslated_text_set.add(item["text"])
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
    untranslated_text_set.update(translated_text_dict.keys())
for lang in untranslated_text_dict.keys():
    for text in untranslated_text_set:
        untranslated_text_dict[lang].setdefault(text, "")
untranslated_text_list = list(untranslated_text_set)


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
    global untranslated_text_list
    print("===== The untranslated text table =====")
    for index, text in enumerate(untranslated_text_list, 1):
        print("{num}.{text}".format(num=index, text=repr(text)))


def printLanguages():
    global supported_languages
    print("===== The supported languages list =====")
    for index, lang in enumerate(supported_languages, 1):
        print(f"{index}.{lang}")


def translateText():
    global untranslated_text_dict, untranslated_text_list
    keep_lang = False
    while True:
        try:
            if not keep_lang:
                lang = input("Please enter the language: ")
                if lang not in untranslated_text_dict.keys():
                    raise ValueError
                keep_lang = askYesOrNo("Keep this language?")
            index = int(input("Please enter the number of the text: ")) - 1
            if not (0 <= index < len(untranslated_text_dict[lang])):
                raise ValueError
        except ValueError:
            print("Your input is invaild. Translation is aborted.",
                  file=sys.stderr)
            break
        untranslated_text = untranslated_text_list[index]
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
    }]
tool_cases_num = len(tool_cases)
while running:
    try:
        print()
        for index, case in enumerate(tool_cases):
            print("{}.".format(index), case["label"])
        op = int(input())
        if not (0 <= op < tool_cases_num):
            raise ValueError
    except ValueError:
        print("Your choice is invaild. Please try again.", file=sys.stderr)
        continue
    print()
    tool_cases[op]["target"]()
if askYesOrNo("Save translation data?"):
    print("Saving translate data ...")
    for lang, lang_data in untranslated_text_dict.items():
        with open(
            os.path.join(tool_constants.lang_path,
                         "{lang}.json".format(lang=lang)),
                'w') as data:
            json.dump(lang_data, data, ensure_ascii=False, indent=4)
