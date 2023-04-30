text = {
    "1": {
        "2": (3, 4),
        "5": [6, 7, 8]
    },
    "9": {
        "10": {11, 12, 13, 14}
    }
}

def output(structure, indent=4):
    if not isinstance(structure, dict):
        print(structure)
        return
    spaces = ' ' * indent
    def outputsub(structure, depth=0):
        nonlocal spaces
        for label, inside in structure.items():
            print(spaces * depth + str(label), end='')
            if isinstance(inside, dict):
                print()
                outputsub(inside, depth + 1)
                continue
            print(' ' + str(inside))
    outputsub(structure)

output(text)
