import os
from fastapi import APIRouter
from dotenv import find_dotenv, load_dotenv

from ..database.db import postgis_query_to_geojson, sql_query_to_json

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
