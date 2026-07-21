import logging
from typing import Self

LOG_FORMAT_TEMPLATE = '\033[33m%(asctime)s\033[0m - \033[36m%(levelname)s\033[0m: \033[37m%(message)s\033[0m'


class LogHandler:
    def __init__(self, log_type: str = 'core') -> None:
        self.logger: logging.Logger = logging.getLogger(log_type)
        self.handler: logging.StreamHandler = logging.StreamHandler()

    async def __aenter__(self: Self) -> Self:
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter(LOG_FORMAT_TEMPLATE)
        self.handler.setFormatter(formatter)
        self.logger.addHandler(self.handler)
        return self

    async def __aexit__(self, exc_type: any, exc: any, tb: any) -> None:
        for handler in self.logger.handlers:
            handler.close()
