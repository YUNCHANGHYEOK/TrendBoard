import signal
import sys
from dotenv import load_dotenv
from backend.server import run_api
from scraper.runtime import start_scheduler

load_dotenv()


def main():
    scheduler = start_scheduler()

    def shutdown(sig, frame):
        scheduler.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    run_api()


if __name__ == "__main__":
    main()
