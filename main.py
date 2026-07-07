import os
import sys


try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "--headless":
        args = args[1:]

    from fh6auto_core.headless import main as headless_main

    return headless_main(args)


if __name__ == "__main__":
    main()
