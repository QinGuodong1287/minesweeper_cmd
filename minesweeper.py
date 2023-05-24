import sys

import core
import pages


def main() -> int:
    while True:
        try:
            core.graphics.init()
            retcode = gamemain()
            break
        except Exception:
            core.logger.logError()
            retcode = 1
        finally:
            core.graphics.end()
            if retcode:
                """print("抱歉，该游戏出现错误，可输入“python3 {}”并按Enter键重新启动游戏。".format(
                    sys.argv[0]))"""
                choice = (input(core.localize.tr("抱歉，该游戏出现错误。是否重新启动游戏？(y/n) "))
                          .lower())
                if not (choice and choice[0] == 'y'):
                    break
    print(core.localize.tr(
        "如需启动游戏，可输入“python3 {}”并按Enter键。").format(sys.argv[0]))
    return retcode


def gamemain() -> int:
    gamewin = pages.mainpage.Minesweeper()
    gamewin.doModel()
    return 0


if __name__ == "__main__":
    sys.exit(main())
