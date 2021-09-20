import os
from fastapi import APIRouter
from dotenv import find_dotenv, load_dotenv

from ..database.db import postgis_query_to_geojson, sql_query_raw, sql_query_to_df

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
) -> list:
    """
    Accept a ID for a point from the ETA dataset

    Return a list of all missing link IDs that intersect the OSM
    """

    query = f"""
        with bounds as (
            select geom
            from api.isochrones
            where eta_uid = '{int(q)}'
            and src_network = 'osm_edges_all_no_motorway'
        )
        select
            ml.uid
        from api.missing_links ml, bounds b
        where st_intersects(ml.geom, b.geom)
    """

    data = await sql_query_raw(
        query,
        DATABASE_URL,
    )

    return [v for d in data for _, v in d.items()]


@sidewalk_router.get("/gaps-within-muni/")
async def get_missing_links_inside_muni(
    q: str,
) -> list:
    """
    Get missing gap IDs within a municipality
    """

    if ";" in q:
        return None

    query = f"""
        with bounds as (
            select geom
            from api.montco_munis
            where mun_name = '{q}'
        )
        select
            ml.uid
        from api.missing_links ml, bounds b
        where st_intersects(ml.geom, b.geom)
    """

    data = await sql_query_raw(
        query,
        DATABASE_URL,
    )

    return [v for d in data for _, v in d.items()]


@sidewalk_router.get("/gaps-near-xy/")
async def get_missing_links_near_xy(
    lng: float,
    lat: float,
) -> list:
    """
    Get missing gaps within 2 miles of lat/lng
    """

    query = f"""
        with bounds as (
            select
                st_transform(
                    st_setsrid(
                        st_point({lng}, {lat}),
                        4326
                    ),
                    26918
                ) as geom
        )
        select
            ml.uid
        from api.missing_links ml, bounds b
        where st_dwithin(ml.geom, b.geom, 3218)
    """

    data = await sql_query_raw(
        query,
        DATABASE_URL,
    )
    return [v for d in data for _, v in d.items()]


@sidewalk_router.get("/all-munis/")
async def get_all_munis() -> dict:
    """
    Return a geojson with all municipalities in Montgomery County
    """

    query = """
        select
            mun_name,
            st_transform(geom, 4326) as geometry
        from
            api.montco_munis
    """

    return await postgis_query_to_geojson(
        query,
        ["mun_name", "geometry"],
        DATABASE_URL,
    )


@sidewalk_router.get("/one-muni/")
async def get_one_muni(
    q: str,
) -> dict:
    """
    Accept a string for municpality name

    Return a geojson with one shape
    """

    if ";" in q:
        return None

    query = f"""
        select
            mun_name,
            st_transform(geom, 4326) as geometry
        from
            api.montco_munis
        where
            mun_name = '{q}'
    """

    return await postgis_query_to_geojson(
        query,
        ["mun_name", "geometry"],
        DATABASE_URL,
    )


@sidewalk_router.get("/one-muni-centroid/")
async def get_one_muni_centroid(
    q: str,
) -> dict:
    """
    Accept a string for municpality name

    Return json with X/Y value for the centroid
    """

    if ";" in q:
        return None

    query = f"""
		with point as (
	        select
                st_centroid(st_transform(geom, 4326)) as geom
            from
                api.montco_munis
            where
                mun_name = '{q}'	
		)
		select
            st_x(geom) as x,
            st_y(geom) as y
		from point
    """

    return await sql_query_raw(
        query,
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


@sidewalk_router.get("/pois-near-gap/")
async def get_poi_uids_near_gap_segment(
    q: int,
) -> dict:
    """Get a list of unique IDs of POIs that a sidewalk gap would help with"""
    query = f"""
    with sw as (
        select
            geom
        from
            api.missing_links
        where
            uid = {int(q)}
    ),
    poi_uids as (
        select distinct i.eta_uid as poi_uid from api.isochrones i, sw
        where st_within(sw.geom, i.geom)
        and src_network = 'osm_edges_all_no_motorway'
    )
    select
        array_agg(p.poi_name) as poi_name,
        p.category,
        p.ab_ratio,
        st_transform(p.geom, 4326) as geometry
    from api.pois p
    inner join
        poi_uids u
      on p.poi_uid::text = u.poi_uid
    group by p.category, p.geom, p.ab_ratio
    """

    return await postgis_query_to_geojson(
        query,
        ["poi_name", "category", "ab_ratio", "geometry"],
        DATABASE_URL,
    )


@sidewalk_router.get("/pois-near-existing-sidewalk/")
async def get_poi_uids_near_existing_sidewalk(lng: float, lat: float) -> dict:
    """Get a geojson of all POIs that have OSM walksheds intersecting a given lng/lat"""
    query = f"""
    with sw as (
        select
            st_transform(
                st_setsrid(
                    st_point({lng}, {lat}),
                    4326
                ),
                26918
            ) as geom
    ),
    poi_uids as (
        select distinct i.eta_uid as poi_uid from api.isochrones i, sw
        where st_within(sw.geom, i.geom)
        and src_network = 'osm_edges_all_no_motorway'
    )
    select
        array_agg(p.poi_name) as poi_name,
        p.category,
        p.ab_ratio,
        st_transform(p.geom, 4326) as geometry
    from api.pois p
    inner join
        poi_uids u
      on p.poi_uid::text = u.poi_uid
    group by p.category, p.geom, p.ab_ratio
    """

    return await postgis_query_to_geojson(
        query,
        ["poi_name", "category", "ab_ratio", "geometry"],
        DATABASE_URL,
    )
