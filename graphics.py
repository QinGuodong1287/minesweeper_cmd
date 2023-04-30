import math
import collections
import os
import curses

stdscr = None

WHITE = 0
RED = 1
GREEN = 2
BLUE = 4
CYAN = 6

def init():
    global stdscr
    stdscr = curses.initscr()
    curses.curs_set(0)
    curses.noecho()
    curses.start_color()
    stdscr.keypad(True)
    global WHITE, RED, GREEN, BLUE, CYAN
    curses.init_pair(RED, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(GREEN, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(BLUE, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(CYAN, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(WHITE + 10, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(GREEN + 10, curses.COLOR_BLACK, curses.COLOR_GREEN)
    curses.init_pair(RED + 10, curses.COLOR_BLACK, curses.COLOR_RED)
    curses.init_pair(BLUE + 10, curses.COLOR_BLACK, curses.COLOR_BLUE)
    curses.init_pair(CYAN + 10, curses.COLOR_BLACK, curses.COLOR_CYAN)
    global COLOR_WHITE, COLOR_RED, COLOR_GREEN, COLOR_BLUE, COLOR_CYAN
    COLOR_WHITE = curses.color_pair(WHITE)
    COLOR_RED = curses.color_pair(RED)
    COLOR_GREEN = curses.color_pair(GREEN)
    COLOR_BLUE = curses.color_pair(BLUE)
    COLOR_CYAN = curses.color_pair(CYAN)
    global KEY_BACKSPACE
    KEY_BACKSPACE = 127

def end():
    global stdscr
    curses.endwin()
    stdscr = None

Point = collections.namedtuple("Point", ("x", "y"))
Size = collections.namedtuple("Size", ("width", "height"))

class Widget:
    def __init__(self, x=None, y=None, width=None, height=None, parent=None, pad_mode=True, **attrs):
        if parent is not None and not isinstance(parent, Widget):
            raise ValueError("The parent window is not a Widget instance.")
        global stdscr
        self.geometry = {"x": x, "y": y, "width": width, "height": height}
        self.attrs = attrs
        self.pad_mode = bool(pad_mode)
        self.parent = parent
        self.children = []
        self.__fix_geometry()
        self.last_geometry = {}
        self.last_geometry.update(self.geometry)
        self.terminal_size = os.get_terminal_size()
        if parent is not None and self not in self.parent.children:
            self.parent.children.append(self)
        self.initWin()
        self.running = False
        self.error = False
        self.show = True
        self.repaint = False

    def __fix_geometry(self):
        self.terminal_size = terminal_size = os.get_terminal_size()
        self.geometry["x"] = max(int(self.geometry["x"]), 0 if self.pad_mode else -math.inf) if self.geometry["x"] is not None else 0
        self.geometry["y"] = max(int(self.geometry["y"]), 0 if self.pad_mode else -math.inf) if self.geometry["y"] is not None else 0
        self.geometry["width"] = max(int(self.geometry["width"]), 1) if self.geometry["width"] is not None else terminal_size.columns
        self.geometry["height"] = max(int(self.geometry["height"]), 1) if self.geometry["height"] is not None else terminal_size.lines
        self.geometry["real_x"] = (self.parent.geometry["real_x"] if self.parent is not None and "real_x" in self.parent.geometry else 0) + self.geometry["x"]
        self.geometry["real_y"] = (self.parent.geometry["real_y"] if self.parent is not None and "real_y" in self.parent.geometry else 0) + self.geometry["y"]

    def initWin(self):
        self.__fix_geometry()
        if hasattr(self, "win") and self.win is not None:
            if isinstance(self.win, curses.window):
                return
            del self.win
        global stdscr
        self.parwin = parwin = stdscr if self.parent is None else self.parent.win
        parwinpos, parwinsize = parwin.getbegyx(), parwin.getmaxyx()
        x = min(self.geometry["real_x"], self.terminal_size.columns - 1)
        y = min(self.geometry["real_y"], self.terminal_size.lines - 1)
        width = min(self.geometry["width"], self.terminal_size.columns - x) if self.geometry["width"] is not None else self.terminal_size.columns
        height = min(self.geometry["height"], self.terminal_size.lines - y) if self.geometry["height"] is not None else self.terminal_size.lines
        self.win = (curses.newpad if self.pad_mode else curses.newwin)(height, width, y, x)
        self.win.overwrite(parwin)
        self.win.erase()
        self.win.refresh()
        self.win.keypad(True)
        parwin.touchwin()
        parwin.refresh()
        self.repaint = False

    def updateWin(self):
        self.terminal_size = os.get_terminal_size()
        self.__fix_geometry()
        parwinpos, parwinsize = self.parwin.getbegyx(), self.parwin.getmaxyx()
        x = min(max(self.geometry["real_x"], 0), self.terminal_size.columns - 1)
        last_x = min(max(self.last_geometry["real_x"], 0), self.terminal_size.columns - 1)
        y = min(max(self.geometry["real_y"], 0), self.terminal_size.lines - 1)
        last_y = min(max(self.last_geometry["real_y"], 0), self.terminal_size.lines - 1)
        self.win.erase()
        self.win.resize(min(self.geometry["height"], self.terminal_size.lines - max(y, last_y)), min(self.geometry["width"], self.terminal_size.columns - max(x, last_x)))
        self.win.mvwin(y, x)
        self.win.resize(min(self.geometry["height"], self.terminal_size.lines - y), min(self.geometry["width"], self.terminal_size.columns - x))
        self.last_geometry.update(self.geometry)
        self.win.touchwin()
        self.win.refresh()
        self.parwin.touchwin()
        self.parwin.refresh()

    @classmethod
    def convertToRelativePos(cls, parent, x, y):
        if isinstance(parent, Widget):
            parx = parent.geometry["real_x"]
            pary = parent.geometry["real_y"]
        elif isinstance(parent, curses.window):
            pary, parx = parent.getbegyx()
        else:
            raise ValueError("The window is not a Widget or curses.window object.")
        return Point(x=x - parx, y=y - pary)

    @classmethod
    def convertToAbsolutePos(cls, parent, x, y):
        if isinstance(parent, Widget):
            parx = parent.geometry["real_x"]
            pary = parent.geometry["real_y"]
        elif isinstance(parent, curses.window):
            pary, parx = parent.getbegyx()
        else:
            raise ValueError("The window is not a Widget or curses.window object.")
        return Point(x=parx + x, y=pary + y)

    def move(self, x=None, y=None):
        self.geometry["x"] = x
        self.geometry["y"] = y
        self.__fix_geometry()
        self.repaint = True

    def getPos(self):
        parx = self.parent.geometry["real_x"]
        pary = self.parent.geometry["real_y"]
        return Point(x=(parx if not self.pad_mode else 0) + self.geometry["x"], y=(pary if not self.pad_mode else 0) + self.geometry["y"])

    def resize(self, width=None, height=None):
        self.geometry["width"] = width
        self.geometry["height"] = height
        self.__fix_geometry()
        self.repaint = True

    def getSize(self):
        return Size(width=self.geometry["width"], height=self.geometry["height"])

    def setAttr(**attrs):
        self.attrs.update(attrs)

    def refresh(self):
        self.win.noutrefresh()

    def close(self):
        self.running = False
    
    def showWin(self, show=True):
        if show:
            self.show = True
            self.initWin()
        else:
            self.show = False
            del self.win
            self.win = None

    def handleException(self, exc):
        return exc

    def clearError(self):
        self.error = False

    def __getBorder(self):
        border_labels = ("ls", "rs", "ts", "bs", "tl", "tr", "bl", "br")
        borders = {}
        for label in border_labels:
            if label not in self.attrs:
                continue
            bd = self.attrs[label]
            if bd is None:
                num = 0
            elif isinstance(bd, str):
                num = bd
            else:
                num = max(int(bd), 0)
            borders[label] = num
        return borders

    def drawBorder(self):
        borders = self.__getBorder()
        if borders:
            self.win.border(borders.get("ls", 0), borders.get("rs", 0), borders.get("ts", 0), borders.get("bs", 0), borders.get("tl", 0), borders.get("tr", 0), borders.get("bl", 0), borders.get("br", 0))

    def doModel(self):
        if not self.error:
            self.running = True
            self.showWin()
        try:
            while self.running and self.show:
                terminal_size = os.get_terminal_size()
                if terminal_size != self.terminal_size:
                    self.win.erase()
                    self.terminal_size = terminal_size
                self.__fix_geometry()
                self.repaint = False
                try:
                    self.drawBorder()
                    self.eventloop()
                except Exception as e:
                    exc = self.handleException(e)
                    self.error = exc is not None
                    if exc:
                        raise exc
                if self.show:
                    if self.repaint:
                        self.updateWin()
                    else:
                        self.win.refresh()
                if self.error:
                    self.running = False
        finally:
            if not self.running:
                self.forceClose()

    def doNoModel(self):
        if not self.error:
            self.running = True
            self.showWin()
        terminal_size = os.get_terminal_size()
        if terminal_size != self.terminal_size:
            self.win.erase()
            self.terminal_size = terminal_size
        try:
            self.drawBorder()
            self.eventloop()
            if self.show:
                if self.repaint:
                    self.updateWin()
                else:
                    self.win.refresh()
        except Exception as e:
            exc = self.handleException(e)
            self.error = exc is not None
            if exc:
                raise exc
            if not self.running:
                self.forceClose()

    def forceClose(self):
        self.close()
        while self.children:
            self.children.pop().forceClose()
        if hasattr(self, "win") and self.win is not None:
            self.win.erase()
        del self.win
        self.win = None
        del self.parwin
        self.parwin = None
        if self.parent is None:
            return
        if self in self.parent.children:
            self.parent.children.remove(self)

    # This method should be overwrited in the subclass.
    def eventloop(self):
        self.refresh()

class Window(Widget):
    def __init__(self, x=None, y=None, width=None, height=None, parent=None, **attrs):
        super().__init__(x, y, width, height, parent, False, **attrs)
