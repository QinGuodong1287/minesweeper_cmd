import os
import json
import sys
import readline

import tool_constants

print("Initializing tool ...")
readline.clear_history()
with open(os.path.join(tool_constants.lang_path,
                       r"untranslated_text.json")) as log:
    untranslated_text_list = json.load(log)
untranslated_text_dict = {}
for item in untranslated_text_list:
    untranslated_text_dict.setdefault(item["lang"], {})
    untranslated_text_dict[item["lang"]][item["text"]] = ""
for lang in untranslated_text_dict.keys():
    lang_file = os.path.join(tool_constants.lang_path, "{lang}.json".format(
        lang=lang))
    if not os.path.exists(lang_file):
        continue
    with open(lang_file) as file:
        untranslated_text_dict[lang].update(json.load(file))
with open(os.path.join(tool_constants.lang_path, "lang.json")) as settings:
    supported_languages = json.load(settings)["support_languages"]


def askYesOrNo(prompt: str = "", default: bool = True,
               retry: bool = True) -> bool:
    prompt = str(prompt)
    if prompt:
        if "(y/n)" not in prompt.lower():
            choice = "({yes}/{no})".format(
                yes='Y' if default else 'y',
                no='N' if not default else 'n')
            prompt = ' '.join((prompt, choice, ''))
    else:
        prompt = "Please enter y or n: "
    default = bool(default)
    while True:
        user_input = input(prompt).lower()
        if not user_input:
            res = default
            break
        if user_input in ('y', 'n'):
            res = user_input == 'y'
            break
        if not retry:
            res = False
            break
        print("Your input is invaild. Please enter y or n.",
              file=sys.stderr)
    return res


running = True


def exitTool():
    global running
    running = False


def printTextTable():
    global untranslated_text_dict
    print("===== The untranslated text table =====")
    for lang, text_list in untranslated_text_dict.items():
        print("{}:".format(lang))
        for index, text in enumerate(text_list, 1):
            print("\t{num}.{text}".format(num=index, text=repr(text)))


def printLanguages():
    global supported_languages
    print("===== The supported languages list =====")
    for index, lang in enumerate(supported_languages, 1):
        print(f"{index}. {lang}")


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
        untranslated_text = untranslated_text_list[index]["text"]
        print("The text is {}.".format(repr(untranslated_text)))
        translated_text = input("Please enter the translated text:\n")
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
