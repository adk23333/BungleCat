from typing import Optional, Union, Dict, Any

from aiotieba.exception import TiebaServerError, HTTPStatusError
from sanic import SanicException

class InvalidParameter(SanicException):
    """422 Invalid Parameter

    当参数无效时抛出。

    """
    message = "无效参数"
    status_code = 422
    quiet = True

class AioTiebaException(SanicException):
    status_code = 502
    retcode = 0

    def __init__(
        self,
        err: Optional[Union[TiebaServerError, HTTPStatusError]],
        *,
        quiet: Optional[bool] = True,
        context: Optional[Dict[str, Any]] = None,
        extra: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.retcode = err.code
        super().__init__(
            err.msg,
            quiet=quiet,
            context=context,
            extra=extra,
            headers=headers,
        )
