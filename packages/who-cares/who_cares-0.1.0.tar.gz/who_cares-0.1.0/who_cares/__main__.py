"""
Usage:
  who-cares
  who-cares -h|--help
  who-cares --version

"""

import sys

from docopt import docopt, DocoptExit

from who_cares import __version__


def main() -> int:
    try:
        docopt(__doc__, version=__version__)
    except DocoptExit as e:
        print(e.usage.strip(), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    main()
