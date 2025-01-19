import logging
import os
import signal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from module.conf import VERSION
from module.core import Program
from module.models import APIResponse
from module.security.api import UNAUTHORIZED, get_current_user

from .response import u_response

logger = logging.getLogger(__name__)
program = Program()
router = APIRouter(tags=["program"])


@router.on_event("startup")
async def startup():
    logger.info("Starting program...")
    await program.startup()


@router.on_event("shutdown")
async def shutdown():
    logger.info("Stopping program...")
    program.stop()


@router.get(
    "/restart", response_model=APIResponse, dependencies=[Depends(get_current_user)]
)
async def restart():
    try:
        logger.info("Restarting program...")
        resp = await program.restart()
        return u_response(resp)
    except Exception as e:
        logger.debug(e)
        logger.warning("Failed to restart program")
        raise HTTPException(
            status_code=500,
            detail={
                "msg_en": "Failed to restart program.",
                "msg_zh": "重启程序失败。",
            },
        )


@router.get(
    "/start", response_model=APIResponse, dependencies=[Depends(get_current_user)]
)
async def start():
    try:
        logger.info("Starting program...")
        resp = await program.start()
        return u_response(resp)
    except Exception as e:
        logger.debug(e)
        logger.warning("Failed to start program")
        raise HTTPException(
            status_code=500,
            detail={
                "msg_en": "Failed to start program.",
                "msg_zh": "启动程序失败。",
            },
        )


@router.get(
    "/stop", response_model=APIResponse, dependencies=[Depends(get_current_user)]
)
async def stop():
    logger.info("Stopping program...")
    return u_response(program.stop())


@router.get("/status", response_model=dict, dependencies=[Depends(get_current_user)])
async def program_status():
    return {
        "status": program.is_running,
        "version": VERSION,
        "first_run": program.first_run,
    }


@router.get(
    "/shutdown", response_model=APIResponse, dependencies=[Depends(get_current_user)]
)
async def shutdown_program():
    logger.info("Calling shutdown_program")
    program.stop()
    logger.info("Shutting down program...")
    os.kill(os.getpid(), signal.SIGINT)
    return JSONResponse(
        status_code=200,
        content={
            "msg_en": "Shutdown program successfully.",
            "msg_zh": "关闭程序成功。",
        },
    )


# Check status
@router.get(
    "/check/downloader",
    tags=["check"],
    response_model=bool,
    dependencies=[Depends(get_current_user)],
)
async def check_downloader_status():
    return program.check_downloader()
