import curses
stdscr = curses.initscr()
try:
    key = stdscr.getch()
    while key != curses.KEY_MOUSE: pass
    data = curses.getsyx()
finally:
    curses.endwin()
    print(data)
