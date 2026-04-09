import uvicorn
import signal
import sys
from dotenv import load_dotenv
from scraper.main import start_scheduler

load_dotenv()


def main():
    scheduler = start_scheduler()

    def shutdown(sig, frame):
        scheduler.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
