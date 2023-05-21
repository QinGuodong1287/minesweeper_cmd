import sys

import logger
import graphics
import mainpage
import localize


def main() -> int:
    while True:
        try:
            graphics.init()
            retcode = gamemain()
            break
        except Exception:
            logger.logError()
            retcode = 1
        finally:
            graphics.end()
            if retcode:
                """print("抱歉，该游戏出现错误，可输入“python3 {}”并按Enter键重新启动游戏。".format(
                    sys.argv[0]))"""
                choice = (input(localize.tr("抱歉，该游戏出现错误。是否重新启动游戏？(y/n) "))
                          .lower())
                if not (choice and choice[0] == 'y'):
                    break
    print(localize.tr("如需启动游戏，可输入“python3 {}”并按Enter键。").format(sys.argv[0]))
    return retcode


def gamemain() -> int:
    gamewin = mainpage.Minesweeper()
    gamewin.doModel()
    return 0


if __name__ == "__main__":
    sys.exit(main())
