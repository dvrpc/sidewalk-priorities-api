import os
from fastapi import APIRouter
from dotenv import find_dotenv, load_dotenv

from src.db import postgis_query_to_geojson, sql_query_to_json

# Load Bikeshare database URI from .env file
load_dotenv(find_dotenv())
BIKESHARE_DATABASE_URL = os.environ.get("BIKESHARE_DATABASE_URL")


bikeshare_router = APIRouter(
    prefix="/indego",
    tags=["philly bikeshare"],
)


@bikeshare_router.get("/all/")
async def get_all_indego_stations() -> dict:
    """
    Serve a geojson of all station points
    """
    query = """
        select
            id as station_id,
            name,
            addressstreet,
            geom as geometry
        from
            station_shapes
    """
    return await postgis_query_to_geojson(
        query, ["station_id", "name", "addressstreet", "geometry"]
    )


@bikeshare_router.get("/trip-points/")
async def get_trips_for_single_indego_station_as_geojson(
    q: int,
) -> dict:
    """
    Accept a station ID

    Return a geojson with number of trips to/from this station to all others
    """

    query = f"""
    select
        station_id,
        origins::float / 75 as origins,
        destinations::float / 75 as destinations,
        CASE WHEN station_id = {int(q)} THEN origins::float / 75
            ELSE (origins::float + destinations::float) / 75 END as totalTrips,
        geom as geometry from station_{int(q)};
    """

    return await postgis_query_to_geojson(
        query,
        ["station_id", "origins", "destinations", "totalTrips", "geometry"],
        BIKESHARE_DATABASE_URL,
    )


@bikeshare_router.get("/trip-spider/")
async def get_spider_diagram_for_single_indego_station_as_geojson(
    q: int,
) -> dict:
    """
    Accept a station ID

    Return a geojson with number of trips to/from this station to all others
    """

    query = f"""
        with raw as (
            select
                station_id,
                origins::float / 75 as origins,
                destinations::float / 75 as destinations,
                (origins::float + destinations::float) / 75 as totalTrips,
                st_makeline((select geom from station_shapes where id = {int(q)}), geom) as geom 
            from station_{int(q)}
        )
        select station_id, origins, destinations , totalTrips,
        st_setsrid(
            ST_CurveToLine(
                'CIRCULARSTRING(' || st_x(st_startpoint(geom)) || ' ' || st_y(st_startpoint(geom)) || ', ' 
                || st_x(st_centroid(ST_OffsetCurve(geom, st_length(geom)/10, 'quad_segs=4 join=bevel'))) || ' ' || st_y(st_centroid(ST_OffsetCurve(geom, st_length(geom)/10, 'quad_segs=4 join=bevel'))) || ', ' 
                || st_x(st_endpoint(geom)) || ' ' ||  st_y(st_endpoint(geom)) || ')'
            ),
            4326
        ) AS geometry
        from raw
        where station_id != {int(q)}
    """

    return await postgis_query_to_geojson(
        query,
        ["station_id", "origins", "destinations", "totalTrips", "geometry"],
        BIKESHARE_DATABASE_URL,
    )


@bikeshare_router.get("/timeseries/")
async def get_timeseries_data_for_single_station(q: int) -> dict:
    pass

    query = f"""
        with raw as (
            select 
                case when start_station = {int(q)} and end_station = {int(q)} then 'Round Trip'
                when start_station = {int(q)} and end_station != {int(q)} then 'Outbound'
                when start_station != {int(q)} and end_station = {int(q)} then 'Inbound' end as trip_dir,
                *
            from trips_by_quarter
            where start_station = {int(q)} or end_station = {int(q)}
        )
        select trip_dir, y + q as yq, sum(trips) as total_trips
        from raw
        group by trip_dir, y, q
        order by trip_dir, y, q
    """

    return await sql_query_to_json(query, ["trip_dir", "yq", "total_trips"], BIKESHARE_DATABASE_URL)
