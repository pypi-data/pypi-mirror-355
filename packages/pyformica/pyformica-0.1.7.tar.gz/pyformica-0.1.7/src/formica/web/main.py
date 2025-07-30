import asyncio
import logging
from contextlib import asynccontextmanager
from importlib.resources import files

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from formica.settings import app_config
from formica.web.api_routes.main import api_router
from formica.web.web_routes import web_router
from starlette.staticfiles import StaticFiles

@asynccontextmanager
async def lifespan(app_: FastAPI):
    print("Starting up")
    yield
    print("Shutting down")


app = FastAPI(lifespan=lifespan)
logger = logging.getLogger(__name__)

origins = [
    "*",
]
_assets_dir = files("formica.web.dist").joinpath("assets")
app.mount(
    "/assets", StaticFiles(directory=str(_assets_dir)), name="assets"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(web_router, prefix="")


def run_webserver():
    import uvicorn
    try:
        uvicorn.run(
            "formica.web.main:app",
            host=app_config.get("webserver", "HOST"),
            port=app_config.getint("webserver", "PORT"),
            reload=False,
        )
    except KeyboardInterrupt:
        logger.info("Uvicorn server interrupted. Exiting gracefully.")
    except asyncio.CancelledError:
        print("Cancelled during shutdown")


if __name__ == "__main__":
    run_webserver()
