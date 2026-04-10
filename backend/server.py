import os

import uvicorn
from dotenv import load_dotenv

load_dotenv()


def run_api() -> None:
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("backend.app:app", host=host, port=port, reload=False)


def main() -> None:
    run_api()


if __name__ == "__main__":
    main()
