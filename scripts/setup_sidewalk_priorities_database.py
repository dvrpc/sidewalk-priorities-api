import os
from dotenv import find_dotenv, load_dotenv

from .helpers import copy_local_tables_to_cloud

load_dotenv(find_dotenv())

DB_URIS = {
    "cloud": os.environ.get("SUPERUSER_SIDEWALK_PRIORITIES_DATABASE_URL"),
    "local": os.environ.get("LOCAL_SIDEWALK_PRIORITIES_DATABASE_URL"),
}
TABLES_TO_COPY = ["api.missing_links", "api.isochrones"]


def main() -> None:
    """
    - Copy the necessary sidewalk and ischrone tables
    """

    copy_local_tables_to_cloud(TABLES_TO_COPY, DB_URIS["local"], DB_URIS["cloud"])


if __name__ == "__main__":
    main()
