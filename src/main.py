from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .bikeshare.routes import bikeshare_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bikeshare_router)


@app.on_event("startup")
async def startup():
    await db.connect()

    # for sql_cmd in startup_commands:

    #     await db.execute(query=sql_cmd)


@app.on_event("shutdown")
async def shutdown():

    await db.disconnect()
