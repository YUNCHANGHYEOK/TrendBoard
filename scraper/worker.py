import argparse
import signal
from threading import Event

from dotenv import load_dotenv

from scraper.runtime import collect_and_save, start_scheduler

load_dotenv()


def main() -> None:
    parser = argparse.ArgumentParser(description="TrendBoard collection worker")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single collection cycle and exit.",
    )
    args = parser.parse_args()

    if args.once:
        collect_and_save()
        return

    scheduler = start_scheduler()
    stop_event = Event()

    def shutdown(*_: object) -> None:
        if scheduler.running:
            scheduler.shutdown(wait=False)
        stop_event.set()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    stop_event.wait()


if __name__ == "__main__":
    main()
