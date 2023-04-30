import curses

import graphics

number = 0
max_num = 3
running = True

class Demo(graphics.Window):
    def __init__(self):
        super().__init__(x=1, y=1, ts=None)
        self.win.attron(curses.color_pair(graphics.GREEN))

    def eventloop(self):
        self.win.addstr(1, 1, "666", curses.A_NORMAL)
        key = self.win.getch()
        x = self.geometry["x"]
        y = self.geometry["y"]
        width = self.geometry["width"]
        height = self.geometry["height"]
        if key == ord('q'):
            global running
            running = False
            return
        if key == curses.KEY_UP:
            y = max(y - 1, 0)
        elif key == curses.KEY_DOWN:
            y += 1
        elif key == curses.KEY_LEFT:
            x = max(x - 1, 0)
        elif key == curses.KEY_RIGHT:
            x += 1
        elif key == ord('-'):
            width -= 1
            height -= 1
        elif key == ord('+'):
            width += 1
            height += 1
        if key == ord('\t'):
            global number, max_num
            number = (number + 1) % max_num
        self.move(x, y)
        self.resize(width, height)

print("Starting demo...")
graphics.init()
try:
    graphics.stdscr.addstr(0, 0, "666", curses.A_NORMAL)
    graphics.stdscr.refresh()
    demolist = []
    for _ in range(max_num):
        demolist.append(Demo())
    while running:
        demolist[number].doNoModel()
    while demolist:
        demolist[0].forceClose()
        del demolist[0]
finally:
    graphics.end()
