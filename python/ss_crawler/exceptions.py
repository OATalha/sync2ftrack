class SSCrawlerException(Exception):
    pass


class UnknownValue(SSCrawlerException):
    pass


class InvalidState(SSCrawlerException):
    pass


class CacheException(SSCrawlerException):
    pass


class DownloadException(SSCrawlerException):
    pass


class DownloadTimeout(DownloadException):
    pass


class DownloadNotDetected(DownloadException):
    pass