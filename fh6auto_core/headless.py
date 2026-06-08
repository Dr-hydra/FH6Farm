import argparse

from .config import ensure_config_file


VALID_STEPS = ("race", "buy", "cj", "sell")


def run_headless(bot_cls, start_step=None):
    """Run the legacy automation class as a hidden core process."""
    app = bot_cls()
    app.headless_mode = True
    app.withdraw()

    if start_step:
        app.after(800, lambda: app.start_pipeline(start_step))

    app.mainloop()


def main(argv=None):
    parser = argparse.ArgumentParser(description="FH6Auto headless automation core")
    parser.add_argument("--start", choices=VALID_STEPS, help="pipeline step to start")
    args = parser.parse_args(argv)

    ensure_config_file()

    from main import FH_UltimateBot

    run_headless(FH_UltimateBot, args.start)


if __name__ == "__main__":
    main()
