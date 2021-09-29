from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .sidewalk_priorities.routes_sidewalk_priorities import sidewalk_router
from .config import URL_ROOT

app = FastAPI(docs_url=f"{URL_ROOT}/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(sidewalk_router)


@app.on_event("startup")
async def startup():
    pass


@app.on_event("shutdown")
async def shutdown():
    pass


@app.get(URL_ROOT)
async def root():
    return {
        "message": "Welcome to the Sidewalk Priorities API. Add /docs to this URL to see all available API routes."
    }
