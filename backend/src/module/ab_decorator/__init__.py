import logging
import threading
import time
from functools import wraps

from .timeout import timeout

logger = logging.getLogger(__name__)
lock = threading.Lock()


def qb_connect_failed_wait(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        times = 0
        while times < 5:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.debug(f"URL: {args[0]}")
                logger.warning(e)
                logger.warning("Cannot connect to qBittorrent. Wait 5 min and retry...")
                time.sleep(300)
                times += 1

    return wrapper


def api_failed(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.debug(f"URL: {args[0]}")
            logger.warning("Wrong API response.")
            logger.debug(e)

    return wrapper


def locked(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        with lock:
            return func(*args, **kwargs)

    return wrapper


def singleton(cls):
    """
    单例模式的装饰器
    """
    _instances = {}

    @wraps(cls)
    def _singleton(*args, **kwargs):
        if cls not in _instances:
            _instances[cls] = cls(*args, **kwargs)
        return _instances[cls]

    return _singleton


class SingletonType(type):
    """
    单例模式的元类
    """

    _instance_lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            with SingletonType._instance_lock:
                if not hasattr(cls, "_instance"):
                    cls._instance = super().__call__(*args, **kwargs)
        return cls._instance


def run_in_thread(func):
    """
    在线程中运行的装饰器
    """

    @wraps(func)
    def _run_in_thread(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True  # 设置为守护线程
        thread.start()
        return thread

    return _run_in_thread


def run_in_async(func):
    """
    在异步中运行的装饰器
    """

    @wraps(func)
    async def _run_in_async(*args, **kwargs):
        return await func(*args, **kwargs)

    return _run_in_async
