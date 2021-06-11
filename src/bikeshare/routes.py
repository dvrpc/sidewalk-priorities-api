import os
from fastapi import APIRouter
from dotenv import find_dotenv, load_dotenv

import os
import json
import asyncpg
import shapely
import pandas
import geopandas

# from src.db import postgis_query_to_geojson, sql_query_to_json

# Load Bikeshare database URI from .env file
load_dotenv(find_dotenv())
# BIKESHARE_DATABASE_URL = os.environ.get("BIKESHARE_DATABASE_URL")
DATABASE_URL = os.environ.get("DATABASE_URL")


def encode_geometry(geometry):
    """
    Transform `shapely.geometry' into PostGIS type
    """
    if not hasattr(geometry, "__geo_interface__"):
        raise TypeError("{g} does not conform to " "the geo interface".format(g=geometry))

    shape = shapely.geometry.asShape(geometry)
    return shapely.wkb.dumps(shape)


def decode_geometry(wkb):
    """
    Transform PostGIS type into `shapely.geometry'
    """
    return shapely.wkb.loads(wkb)


async def postgis_query_to_geojson(query: str, columns: list, uri: str):
    """
    Connect to postgres via `asyncpg` and return spatial query output
    as a geojson file
    """
    conn = await asyncpg.connect(uri)

    try:

        await conn.set_type_codec(
            "geometry",
            encoder=encode_geometry,
            decoder=decode_geometry,
            format="binary",
        )

        result = await conn.fetch(query)

    finally:
        await conn.close()

    gdf = geopandas.GeoDataFrame.from_records(result, columns=columns)

    return json.loads(gdf.to_json())


async def sql_query_to_json(query: str, columns: list, uri: str):
    """
    Connect to postgres via `asyncpg` and return spatial query output
    as a geojson file
    """
    conn = await asyncpg.connect(uri)

    try:
        result = await conn.fetch(query)

    finally:
        await conn.close()

    df = pandas.DataFrame.from_records(result, columns=columns)

    output = {}

    for val in df["trip_dir"].unique():
        output[val] = {}

        filtered = df[df["trip_dir"] == val]

        output[val]["labels"] = list(str(x).replace(".", " Q") for x in filtered["yq"])
        output[val]["data_values"] = list(filtered["total_trips"])

    return output


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
        query,
        ["station_id", "name", "addressstreet", "geometry"],
        DATABASE_URL,
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
        DATABASE_URL,
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
        DATABASE_URL,
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

    return await sql_query_to_json(query, ["trip_dir", "yq", "total_trips"], DATABASE_URL)
