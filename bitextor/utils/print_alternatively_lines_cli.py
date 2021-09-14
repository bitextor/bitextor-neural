#!/usr/bin/env python3

import sys

from common import print_alternatively_lines

if __name__ == "__main__":
    blocks = 2

    if len(sys.args) > 1:
        blocks = int(sys.args[1])

    print_alternatively_lines(input_file="-", blocks=blocks)
