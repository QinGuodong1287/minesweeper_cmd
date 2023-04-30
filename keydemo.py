import curses

stdscr = curses.initscr()
key = stdscr.getch()
curses.endwin()
print(key)
