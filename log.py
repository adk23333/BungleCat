import logging

from sanic.log import logger
import aiotieba
from typing_extensions import override
from tortoise import log


class NameFilter(logging.Filter):
    @override
    def filter(self, record):
        record.msg = f"<{record.name.split('.')[-1]}> {record.msg}"
        return True

tieba_logger = logger.getChild("aiotieba")
tieba_logger.addFilter(NameFilter())
aiotieba.logging.set_logger(tieba_logger)

orm_logger = logger.getChild("orm")
orm_logger.addFilter(NameFilter())
log.logger = orm_logger