import os


def copy_local_tables_to_cloud(list_of_tablenames: list, local_uri: str, cloud_uri: str) -> None:
    """
    - For each table in `list_of_tablenames`, run a terminal command to pipe data from local DB to cloud DB
    - Command uses:
        > pg_dump LOCAL_URI -t TABLENAME --no-owner | psql CLOUD_URI
    """

    for table in list_of_tablenames:
        cmd = f"pg_dump {local_uri} -t {table} --no-owner | psql {cloud_uri}"

        print(cmd)
        os.system(cmd)
