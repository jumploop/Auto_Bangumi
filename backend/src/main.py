import logging
import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from module.api import v1
from module.conf import VERSION, settings, setup_logger

setup_logger(reset=True)
logger = logging.getLogger(__name__)
uvicorn_logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": logger.handlers,
    "loggers": {
        "uvicorn": {
            "level": logger.level,
        },
        "uvicorn.access": {
            "level": "WARNING",
        },
    },
}


def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(v1, prefix="/api")
    if VERSION != "DEV_VERSION":
        app.mount("/assets", StaticFiles(directory="dist/assets"), name="assets")
        app.mount("/images", StaticFiles(directory="dist/images"), name="images")
        templates = Jinja2Templates(directory="dist")

        @app.get("/{path:path}")
        async def html(request: Request, path: str):
            file_path = Path("dist") / path
            if file_path.is_file():
                return FileResponse(file_path)
            return templates.TemplateResponse("index.html", {"request": request})
    else:
        @app.get("/", status_code=302, tags=["html"])
        async def index():
            return RedirectResponse("/docs")

    @app.get("/posters/{path:path}", tags=["posters"])
    async def posters(path: str):
        return FileResponse(f"data/posters/{path}")

    return app


app = create_app()

if __name__ == "__main__":
    host = "::" if os.getenv("IPV6") else os.getenv("HOST", "0.0.0.0")
    # 记录 Web 服务器启动信息
    logger.info(f"Starting Web server on {host}:{settings.program.webui_port}")
    uvicorn.run(
        app,
        host=host,
        port=settings.program.webui_port,
        log_config=uvicorn_logging_config,
    )
