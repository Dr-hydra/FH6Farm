import argparse

from .config import ensure_config_file
from .windows_dependencies import check_windows_dependencies


VALID_STEPS = ("race", "buy", "cj", "sell")


def run_headless(bot_cls=None, start_step=None):
    """Run the automation core without constructing the legacy UI."""
    if bot_cls is None:
        check_windows_dependencies()
        from .headless_bot import HeadlessAutomationBot

        bot_cls = HeadlessAutomationBot

    app = bot_cls()

    if start_step:
        app.after(800, lambda: app.start_pipeline(start_step))

    app.mainloop()


def main(argv=None):
    parser = argparse.ArgumentParser(description="FH6Auto headless automation core")
    parser.add_argument("--start", choices=VALID_STEPS, help="pipeline step to start")
    args = parser.parse_args(argv)

    ensure_config_file()
    run_headless(start_step=args.start)


if __name__ == "__main__":
    main()
