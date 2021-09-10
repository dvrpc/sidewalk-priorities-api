import os
from dotenv import find_dotenv, load_dotenv


load_dotenv(find_dotenv())

DB_URIS = {
    "cloud": os.environ.get("SUPERUSER_SIDEWALK_PRIORITIES_DATABASE_URL"),
    "local": os.environ.get("LOCAL_SIDEWALK_PRIORITIES_DATABASE_URL"),
}
TABLES_TO_COPY = [
    # "api.missing_links",
    # "api.isochrones",
    # "api.montco_munis",
    "api.pois",
]


def main() -> None:
    """
    - Copy the necessary sidewalk, isochrone, and municipality tables
    """

    for table in TABLES_TO_COPY:
        cmd = f"pg_dump {DB_URIS['local']} -t {table} --no-owner | psql {DB_URIS['cloud']}"

        print(cmd)
        os.system(cmd)


if __name__ == "__main__":
    main()
