# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import readline
from MathExpression import *


def command_line():
    import sys

    mathExp = MathExp()
    while True:
        try:
            line = input(">>> ")
            if line.strip() == "quit":
                return
            result = mathExp.eval(line)
            if result:
                print(result)
        except EOFError:
            return
        except KeyboardInterrupt:
            sys.stdout.write("\nUse quit to exit!\n")
            continue
        except Exception as err:
            sys.stderr.write(err.args[0] + "\n")


if __name__ == "__main__":
    command_line()
