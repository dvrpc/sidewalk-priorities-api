from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from bikeshare.routes import bikeshare_router

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
    pass


@app.on_event("shutdown")
async def shutdown():
    pass


@app.get("/")
async def root():
    return {"message": "Welcome to the OMAD api. Visit /docs to see all available API routes."}
