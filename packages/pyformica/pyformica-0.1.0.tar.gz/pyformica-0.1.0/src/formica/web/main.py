import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from formica.web.api_routes.main import api_router
from formica.web.web_routes import web_router

app = FastAPI()
logger = logging.getLogger(__name__)

origins = [
    "*",
]

# app.mount("/assets", StaticFiles(directory="ui_formica/dist/assets"), name="assets")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
# app.include_router(web_router, prefix="")


def run_webserver(port=8000):
    import uvicorn

    uvicorn.run("formica.web.main:app", host="127.0.0.1", port=port, reload=True)


if __name__ == "__main__":
    run_webserver()
