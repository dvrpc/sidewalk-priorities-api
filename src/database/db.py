import json
import asyncpg
import shapely
import pandas
import geopandas


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
    Connect to postgres via `asyncpg`

    TODO: refactor business logic out of this function
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


async def sql_query_to_df(query: str, columns: list, uri: str) -> pandas.DataFrame:
    """
    Connect to postgres via `asyncpg` and return a NON-spatial dataframe
    """
    conn = await asyncpg.connect(uri)

    try:
        result = await conn.fetch(query)

    finally:
        await conn.close()

    return pandas.DataFrame.from_records(result, columns=columns)


async def sql_query_raw(query: str, uri: str):
    """
    Connect to postgres via `asyncpg` and return raw result of query
    """
    conn = await asyncpg.connect(uri)

    try:
        result = await conn.fetch(query)

    finally:
        await conn.close()

    return result
