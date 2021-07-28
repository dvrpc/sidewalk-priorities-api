import os
from fastapi import APIRouter
from dotenv import find_dotenv, load_dotenv

from ..database.db import postgis_query_to_geojson, sql_query_to_df

# Load database URI from .env file
load_dotenv(find_dotenv())
DATABASE_URL = os.environ.get("SUPERUSER_SIDEWALK_PRIORITIES_DATABASE_URL")


sidewalk_router = APIRouter(
    prefix="/sidewalk",
    tags=["sidewalk priorities"],
)


@sidewalk_router.get("/nearby-gaps/")
async def get_missing_links_near_poi(
    q: int,
) -> dict:
    """
    Accept a ID for a point from the ETA dataset

    Return a geojson all missing links that intersect the OSM
    """

    query = f"""
        with bounds as (
            select geom
            from api.isochrones
            where eta_uid = '{int(q)}'
            and src_network = 'osm_edges_all_no_motorway'
        )
        select
            ml.uid,
            st_transform(ml.geom, 4326) as geometry
        from api.missing_links ml, bounds b
        where st_intersects(ml.geom, b.geom)
    """

    return await postgis_query_to_geojson(
        query,
        ["uid", "geometry"],
        DATABASE_URL,
    )


@sidewalk_router.get("/walkshed-area/")
async def get_walkshed_areas_for_poi(
    q: int,
) -> dict:
    """
    Accept a ID for a point from the ETA dataset

    Return a json with the area of each polygon walkshed for that point
    """

    query = f"""
        select
            src_network,
            st_area(geom) * 3.86102e-7 as area_sq_miles
        from
            api.isochrones
        where
            eta_uid = '{int(q)}'
    """

    df = await sql_query_to_df(query, ["src_network", "area_sq_miles"], DATABASE_URL)

    # Dump dataframe contents into dictionary
    output = {}
    for _, row in df.iterrows():
        output[row.src_network] = {"area_in_square_miles": row.area_sq_miles}

    # Make sure all responses have two values, even if it's a zero
    for expected_key in ["pedestriannetwork_lines", "osm_edges_all_no_motorway"]:
        if expected_key not in output:
            output[expected_key] = {"area_in_square_miles": [0]}

    return output
