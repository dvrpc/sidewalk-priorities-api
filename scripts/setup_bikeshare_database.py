import os
import asyncio
import asyncpg
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())
BIKESHARE_DATABASE_URL = os.environ.get("BIKESHARE_DATABASE_URL")


MATERIALIZED_VIEWS = [
    # TURN RAW TRIP TABLE INTO SIMPLIFIED TABLE
    """
    create materialized view if not exists 
    trips_simplified
    as
        select
            start_station, end_station,
            extract(year from start_time::timestamp) as y,
            extract(month from start_time::timestamp) as m,
            extract(day from start_time::timestamp) as d,
            extract(hour from start_time::timestamp) as h
        from trips;
    """,
    # ROLL UP SIMPLIFIED TABLE INTO YEAR/QUARTER
    """
    create materialized view if not exists
    trips_by_quarter
    as
        select start_station, end_station, y,
            case when m < 4 then 0.1
            when m < 7 then 0.2
            when m < 10 then 0.3
            else 0.4 end as q,
            count(*) as trips
        from trips_simplified
        group by start_station, end_station, y, q;
    """,
]


QUERY_TEMPLATE = """
    with origins as (
    select
        start_station as station_id,
        count(*) as origins
        from trips_simplified
        where end_station = STATION_ID
        group by start_station
    ),
    destinations as (
    select
        end_station as station_id,
        count(*) as destinations
        from trips_simplified
        where start_station = STATION_ID
        group by end_station
    ),
    numeric_data as (
        select o.station_id, o.origins, d.destinations
        from origins o
        full outer join destinations d on o.station_id = d.station_id
    )
    select ss.geom, ss.name, nd.* from station_shapes ss
    inner join numeric_data nd on ss.id = nd.station_id
"""


async def main():

    conn = await asyncpg.connect(BIKESHARE_DATABASE_URL)

    for view_q in MATERIALIZED_VIEWS:
        await conn.execute(view_q)

    ids = await conn.fetch("SELECT DISTINCT id FROM station_shapes ORDER BY id asc")

    for id in ids:
        station_id = id["id"]
        print("Starting", station_id)

        await conn.execute(query=f"DROP TABLE IF EXISTS station_{station_id};")

        query = f"""
            CREATE TABLE station_{station_id} AS
        """ + QUERY_TEMPLATE.replace(
            "STATION_ID", str(station_id)
        )

        await conn.execute(query=query)

        print("... completed", station_id)

    await conn.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
