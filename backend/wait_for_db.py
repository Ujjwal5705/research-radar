"""Poll the database until it accepts connections. Used by entrypoint.sh
before running migrations, so we don't race Postgres's startup even if
Docker's healthcheck timing is ever slightly off."""

import sys
import time

from sqlalchemy import create_engine, text

from app.config import settings

MAX_ATTEMPTS = 30
DELAY_SECONDS = 2


def main() -> None:
    engine = create_engine(settings.database_url)
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("Database is ready.")
            return
        except Exception as e:
            print(f"Waiting for database... ({attempt}/{MAX_ATTEMPTS}) {e}")
            time.sleep(DELAY_SECONDS)
    print("Database never became available.", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
