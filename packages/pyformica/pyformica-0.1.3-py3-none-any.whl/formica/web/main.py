import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from formica.settings import config
from formica.web.api_routes.main import api_router
from formica.web.web_routes import web_router

app = FastAPI()
logger = logging.getLogger(__name__)

origins = [
    "*",
]

# app.mount("/assets", StaticFiles(directory="src/formica/web/dist/assets"), name="assets")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
# app.include_router(web_router, prefix="")


def run_webserver():
    import uvicorn

    uvicorn.run("formica.web.main:app", host=config.get("webserver", "HOST"), port=config.getint("webserver", "PORT"), reload=True)


if __name__ == "__main__":
    run_webserver()
