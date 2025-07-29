import json
import os

import psycopg_pool
from fastapi import FastAPI, Response, HTTPException

import tilekiln
from tilekiln.config import Config
from tilekiln.kiln import Kiln
from tilekiln.tile import Tile
from tilekiln.tileset import Tileset
from tilekiln.storage import Storage

HTTP_TIME = "%a, %d %b %Y %H:%M:%S GMT"

# Constants for MVTs
MVT_MIME_TYPE = "application/vnd.mapbox-vector-tile"

# Constants for environment variable names
# Passing around enviornment variables really is the best way to get this to fastapi
TILEKILN_CONFIG = "TILEKILN_CONFIG"
TILEKILN_URL = "TILEKILN_URL"
TILEKILN_THREADS = "TILEKILN_THREADS"

STANDARD_HEADERS: dict[str, str] = {"Access-Control-Allow-Origin": "*",
                                    "Access-Control-Allow-Methods": "GET, HEAD"}

kiln: Kiln
config: Config
storage: Storage
tilesets: dict[str, Tileset] = {}

# Two types of server are defined - one for static tiles, the other for live generated tiles.
server = FastAPI()
live = FastAPI()

# TODO: Set up middleware for CORS


# TODO: Move elsewhere
def change_tilejson_url(tilejson: str, baseurl: str) -> str:
    modified_tilejson = json.loads(tilejson)
    modified_tilejson["tiles"] = [baseurl + "/{z}/{x}/{y}.mvt"]
    return json.dumps(modified_tilejson)


@server.on_event("startup")
def load_server_config():
    '''Load the config for the server with static pre-rendered tiles'''
    global storage
    global tilesets
    # Because the DB connection variables are passed as standard PG* vars,
    # a plain ConnectionPool() will connect to the right DB
    conn = psycopg_pool.ConnectionPool(min_size=1, max_size=1, num_workers=1,
                                       check=psycopg_pool.ConnectionPool.check_connection)
    # TODO: Make readonly?

    storage = Storage(conn)
    for tileset in storage.get_tilesets():
        tilesets[tileset.id] = tileset


@live.on_event("startup")
def load_live_config():
    global config
    global storage
    global tilesets
    config = tilekiln.load_config(os.environ[TILEKILN_CONFIG])

    generate_args = {}
    if "GENERATE_PGDATABASE" in os.environ:
        generate_args["dbname"] = os.environ["GENERATE_PGDATABASE"]
    if "GENERATE_PGHOST" in os.environ:
        generate_args["host"] = os.environ["GENERATE_PGHOST"]
    if "GENERATE_PGPORT" in os.environ:
        generate_args["port"] = os.environ["GENERATE_PGPORT"]
    if "GENERATE_PGUSER" in os.environ:
        generate_args["username"] = os.environ["GENERATE_PGUSER"]

    storage_args = {}
    if "STORAGE_PGDATABASE" in os.environ:
        storage_args["dbname"] = os.environ["STORAGE_PGDATABASE"]
    if "STORAGE_PGHOST" in os.environ:
        storage_args["host"] = os.environ["STORAGE_PGHOST"]
    if "STORAGE_PGPORT" in os.environ:
        storage_args["port"] = os.environ["STORAGE_PGPORT"]
    if "STORAGE_PGUSER" in os.environ:
        storage_args["username"] = os.environ["STORAGE_PGUSER"]

    storage_pool = psycopg_pool.ConnectionPool(min_size=1, max_size=1, num_workers=1,
                                               check=psycopg_pool.ConnectionPool.check_connection,
                                               kwargs=storage_args)

    storage = Storage(storage_pool)

    # Storing the tileset in the dict allows some commonalities in code later
    tilesets[config.id] = Tileset.from_config(storage, config)
    generate_pool = psycopg_pool.ConnectionPool(min_size=1, max_size=1, num_workers=1,
                                                check=psycopg_pool.ConnectionPool.check_connection,
                                                kwargs=generate_args)
    global kiln
    kiln = Kiln(config, generate_pool)


@server.head("/")
@server.get("/")
@live.head("/")
@live.get("/")
def root():
    raise HTTPException(status_code=404)


@server.head("/favicon.ico")
@server.get("/favicon.ico")
@live.head("/favicon.ico")
@live.get("/favicon.ico")
def favicon():
    return Response("")


@server.head("/{prefix}/tilejson.json")
@server.get("/{prefix}/tilejson.json")
@live.head("/{prefix}/tilejson.json")
@live.get("/{prefix}/tilejson.json")
def tilejson(prefix: str):
    global tilesets
    if prefix not in tilesets:
        raise HTTPException(status_code=404, detail=f'''Tileset {prefix} not found on server.''')
    return Response(content=change_tilejson_url(tilesets[prefix].tilejson,
                                                os.environ[TILEKILN_URL] + f"/{prefix}"),
                    media_type="application/json",
                    headers=STANDARD_HEADERS)


@server.head("/{prefix}/{zoom}/{x}/{y}.mvt")
@server.get("/{prefix}/{zoom}/{x}/{y}.mvt")
def serve_tile(prefix: str, zoom: int, x: int, y: int):
    global tilesets
    if prefix not in tilesets:
        raise HTTPException(status_code=404, detail=f"Tileset {prefix} not found on server.")

    try:
        tile, generated = tilesets[prefix].get_tile(Tile(zoom, x, y))
    except tilekiln.errors.ZoomNotDefined:
        raise HTTPException(status_code=410,
                            detail=f'''Tileset {zoom} not available for tileset {prefix}.''')

    response = b''
    for data in tile.values():
        if data is None:
            raise HTTPException(status_code=404,
                                detail=f"Tile {prefix}/{zoom}/{x}/{y} not found in storage.")
        response += data

    # We use the generated timestamp on the assumption that a specific
    # x/y/z will not be generated twice in the same ms.
    headers: dict[str, str] = {}
    if generated is not None:
        headers = {"Last-Modified": generated.strftime(HTTP_TIME),
                   "E-tag": generated.strftime("%s.%f")}
    return Response(response, media_type=MVT_MIME_TYPE,
                    headers=STANDARD_HEADERS | headers)


@live.head("/{prefix}/{zoom}/{x}/{y}.mvt")
@live.get("/{prefix}/{zoom}/{x}/{y}.mvt")
def live_serve_tile(prefix: str, zoom: int, x: int, y:  int):
    global tilesets
    if prefix not in tilesets:
        raise HTTPException(status_code=404, detail=f"Tileset {prefix} not found on server.")

    # Attempt to serve a stored tile
    try:
        existing, generated = tilesets[prefix].get_tile(Tile(zoom, x, y))
    except tilekiln.errors.ZoomNotDefined:
        raise HTTPException(status_code=410,
                            detail=f'''Tileset {zoom} not available for tileset {prefix}.''')

    response = b''
    missing = []
    for layer, data in existing.items():
        if data is None:
            missing.append(layer)
        else:
            response += data

    # Handle storage hits
    if missing == []:
        headers: dict[str, str] = {}
        if generated is not None:
            headers = {"Last-Modified": generated.strftime(HTTP_TIME),
                       "E-tag": generated.strftime("%s.%f")}
        return Response(response, media_type=MVT_MIME_TYPE,
                        headers=STANDARD_HEADERS | headers)

    # Storage miss, so generate a new tile
    # TODO: partially generate a new tile
    global kiln
    tile = Tile(zoom, x, y)
    new_layers = {layer: kiln.render_layer(layer, tile) for layer in missing}
    # TODO: Make async so tile is saved and response returned in parallel
    generated = tilesets[prefix].save_tile(tile, new_layers)

    mvt = b''.join(new_layers.values()) + b''.join([data for data in existing.values()
                                                    if data is not None])
    if generated is not None:
        headers = {"Last-Modified": generated.strftime(HTTP_TIME),
                   "E-tag": generated.strftime("%s.%f")}
    else:
        headers = {}

    return Response(mvt,
                    media_type=MVT_MIME_TYPE,
                    headers=STANDARD_HEADERS | headers)
