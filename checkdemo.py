from random import randrange, choice
import json

game_map = [['#' for j in range(10)] for i in range(10)]
mine_map = [[' ' for j in range(10)] for i in range(10)]
mine_num = 0
while mine_num < 50:
    row_num = randrange(10)
    col_num = randrange(10)
    if mine_map[row_num][col_num] == '*':
        continue
    mine_map[row_num][col_num] = '*'
    mine_num += 1

blank_map = []
def detect_map():
    global game_map, mine_map, blank_map, blank_stack
    for rn, row in enumerate(mine_map):
        for cn, block in enumerate(row):
            if block != ' ':
                continue
            flag = False
            for stack in blank_map:
                if rn > 0 and mine_map[rn - 1][cn] == ' ':
                    if (rn - 1, cn) in stack:
                        stack.append((rn, cn))
                        flag = True
                if rn < 9 and mine_map[rn + 1][cn] == ' ':
                    if (rn + 1, cn) in stack:
                        stack.append((rn, cn))
                        flag = True
                if cn > 0 and mine_map[rn][cn - 1] == ' ':
                    if (rn, cn - 1) in stack:
                        stack.append((rn, cn))
                        flag = True
                if cn < 9 and mine_map[rn][cn + 1] == ' ':
                    if (rn, cn + 1) in stack:
                        stack.append((rn, cn))
                        flag = True
            if not flag:
                blank_map.append([(rn, cn)])
    old_map = blank_map[:]
    blank_map.clear()
    for stack in old_map:
        pos_set = set(stack)
        for index, new_stack in enumerate(blank_map):
            new_pos_set = set(new_stack)
            if new_pos_set.isdisjoint(pos_set):
                continue
            new_pos_set.update(pos_set)
            blank_map[index] = list(new_pos_set)
            break
        else:
            blank_map.append(list(pos_set))

def check_pos(row_num, col_num):
    global game_map, blank_map
    pos = (row_num, col_num)
    for stack in blank_map:
        if pos in stack:
            for blank_pos in stack:
                game_map[blank_pos[0]][blank_pos[1]] = mine_map[blank_pos[0]][blank_pos[1]]
            break
    else:
        game_map[pos[0]][pos[1]] = mine_map[pos[0]][pos[1]]

detect_map()
pos = choice(blank_map)[0]
check_pos(pos[0], pos[1])
for line_num in range(10):
    mine_map[line_num] = str(mine_map[line_num])
for num in range(len(blank_map)):
    blank_map[num] = str(blank_map[num])
for num in range(len(game_map)):
    game_map[num] = str(game_map[num])
with open("res.json", "w") as fp:
    json.dump(mine_map, fp, indent=4)
    fp.write('\n')
    json.dump(blank_map, fp, indent=4)
    fp.write('\n')
    json.dump(game_map, fp, indent=4)
