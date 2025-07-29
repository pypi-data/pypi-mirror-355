import os

from fastapi import APIRouter
from starlette.responses import FileResponse

web_router = APIRouter()


# Serve the index.html for the root path and all unmatched routes
@web_router.get("/{full_path:path}")
async def serve_next(full_path: str):
    # If the path exists as a file, serve it directly
    file_path = os.path.join("ui_formica/dist", full_path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)

    # Otherwise return index.html to let React handle the routing
    return FileResponse("ui_formica/dist/index.html")
    # file_path = os.path.join("ui_formica/dist", "index.html")
    # return FileResponse(file_path)
    # # First check if the path exists as a file
    # path_to_next_out = "frontend_formica/out"
    # file_path = os.path.join(path_to_next_out, full_path)
    #
    # if os.path.isfile(file_path):
    #     return FileResponse(file_path)
    #
    # # For paths that don't match a file, serve index.html (for client-side routing)
    # index_path = os.path.join(path_to_next_out, "index.html")
    # return FileResponse(index_path)
