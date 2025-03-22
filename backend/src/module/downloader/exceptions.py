class ConflictError(Exception):
    pass


class DownloadError(Exception):
    """下载异常基类"""

    def __init__(self, message: str, code: int = 500):
        super().__init__(message)
        self.code = code


class TorrentError(DownloadError):
    """种子处理异常"""

    def __init__(self, info_hash: str):
        super().__init__(f"Torrent processing failed: {info_hash}", 400)
