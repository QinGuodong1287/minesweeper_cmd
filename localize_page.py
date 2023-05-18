import curses

import graphics
import tutorial
import localize


class LocalizePage(tutorial.GameTutorialMixin, graphics.Window):
    def __init__(self, parent):
        super().__init__(parent=parent)

    def eventloop(self):
        self.win.addstr(0, 0, localize.tr("切换语言"), curses.A_NORMAL)
        key = self.win.getch(self.terminal_size.lines - 1,
                             self.terminal_size.columns - 1)
        if key == ord('q'):
            self.close()
            return
