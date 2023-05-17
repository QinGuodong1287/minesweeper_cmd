import os
import json
import sys

import constants

print("Initializing tool ...")
with open(os.path.join(constants.lang_path, r"untranslated_text.json")) as log:
    untranslated_text_list = json.load(log)
untranslated_text_dict = {}
for item in untranslated_text_list:
    untranslated_text_dict.setdefault(item["lang"], {})
    untranslated_text_dict[item["lang"]][item["text"]] = ""
for lang in untranslated_text_dict.keys():
    lang_file = os.path.join(constants.lang_path, "{lang}.json".format(
        lang=lang))
    if not os.path.exists(lang_file):
        continue
    with open(lang_file) as file:
        untranslated_text_dict[lang].update(json.load(file))
while True:
    try:
        op = int(input(
            "Please choose an operation (enter the number):\n"
            "0. Exit the tool.\n"
            "1. Print the table.\n"
            "2. Translate a text.\n"
            "3. Retain all texts.\n").lower())
    except ValueError:
        print("Your choice is invaild. Please try again.", file=sys.stderr)
        continue
    if op == 0:
        break
    if op == 1:
        print("===== The untranslated text table =====")
        for lang, text_list in untranslated_text_dict.items():
            print("{}:".format(lang))
            for index, text in enumerate(text_list, 1):
                print("\t{num}.{text}".format(num=index, text=text))
    elif op == 2:
        while True:
            try:
                lang = input("Please enter the language: ")
                if lang not in untranslated_text_dict.keys():
                    raise ValueError
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
            translated_text = eval(repr(translated_text))
            untranslated_text_dict[lang][untranslated_text] = translated_text
            while True:
                choice = (input(
                    "Do you want to translate another text? (Y/n) ")
                    .lower())
                if choice:
                    if choice not in ('y', 'n'):
                        print(
                            "Sorry, your choice is invaild. "
                            "Please enter y or n.",
                            file=sys.stderr)
                    else:
                        break
                else:
                    break
            if choice == 'n':
                break
    elif op == 3:
        lang = input("Please enter the language: ")
        if lang not in untranslated_text_dict.keys():
            print("Your input is invaild. Translation is aborted.",
                  file=sys.stderr)
            continue
        while True:
            choice = input("Retain all texts? (y/N)").lower()
            if not choice:
                break
            if choice == 'y':
                for text in untranslated_text_dict[lang].keys():
                    untranslated_text_dict[lang][text] = text
                break
            elif choice == 'n':
                break
            else:
                print("Your choice is invaild. Please try enter y or n.",
                      file=sys.stderr)
    else:
        print("Your choice is invaild. Please try again.", file=sys.stderr)
choice = input("Save translation data? (Y/n)").lower()
if choice:
    if choice == 'y':
        save = True
    else:
        save = False
else:
    save = True
if save:
    print("Saving translate data ...")
    for lang, lang_data in untranslated_text_dict.items():
        with open(
            os.path.join(constants.lang_path, "{lang}.json".format(lang=lang)),
                'w') as data:
            json.dump(lang_data, data, ensure_ascii=False, indent=4)
