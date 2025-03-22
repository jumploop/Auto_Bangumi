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
# 将 uvicorn 日志配置中的 handlers 部分替换为 formatters
uvicorn_logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(message)s",
            "use_colors": None,
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": '%(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s',
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
    },
}


def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(v1, prefix="/api")

    @app.get("/posters/{path:path}", tags=["posters"])
    async def posters(path: str):
        return FileResponse(f"data/posters/{path}")

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

    return app


app = create_app()

if __name__ == "__main__":
    host = "::" if os.getenv("IPV6") else os.getenv("HOST", "0.0.0.0")
    # 记录 Web 服务器启动信息
    logger.info(f"Starting Web server on {host}:{settings.program.webui_port}")
    uvicorn.run(
        "main:app",
        host=host,
        port=settings.program.webui_port,
        log_config=uvicorn_logging_config,
    )
