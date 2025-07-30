import os

from fastapi import APIRouter
from starlette.responses import FileResponse

web_router = APIRouter()


# Serve the index.html for the root path and all unmatched routes
@web_router.get("/{full_path:path}")
async def serve_next(full_path: str):
    # If the path exists as a file, serve it directly
    file_path = os.path.join("src/formica/web/dist", full_path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)

    # Otherwise return index.html to let React handle the routing
    return FileResponse("src/formica/web/dist/index.html")
