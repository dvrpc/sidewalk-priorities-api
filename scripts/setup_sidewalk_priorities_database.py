import os
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

DB_URLS = {
    "cloud": os.environ.get("SUPERUSER_SIDEWALK_PRIORITIES_DATABASE_URL"),
    "local": os.environ.get("LOCAL_SIDEWALK_PRIORITIES_DATABASE_URL"),
}
TABLES_TO_COPY = ["api.missing_links", "api.isochrones"]


def main() -> None:
    """
    - For each table to copy, run a terminal command to pipe data from local DB to cloud DB
    - Command uses:
        > pg_dump LOCAL_URI -t TABLENAME --no-owner | psql CLOUD_URI
    """

    for table in TABLES_TO_COPY:
        cmd = f"pg_dump {DB_URLS['local']} -t {table} --no-owner | psql {DB_URLS['cloud']}"
        print(cmd)

        os.system(cmd)


if __name__ == "__main__":
    main()
