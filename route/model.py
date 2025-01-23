import json as sys_json
from dataclasses import is_dataclass, asdict
from datetime import datetime
from json import JSONEncoder
from typing import Literal, Optional, Any

import yarl
from aiotieba.exception import TiebaValueError
from pydantic import BaseModel
from sanic import json


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return int(obj.timestamp() * 1000)  # 转换为 13 位时间戳
        elif is_dataclass(obj):
            return asdict(obj)
            # return self.remove_null(asdict(obj))
        # elif isinstance(obj, dict):
        #     return self.remove_null(obj)
        elif isinstance(obj, (TiebaValueError, yarl.URL)):
            return str(obj)
        elif isinstance(obj, BaseModel):
            return obj.model_dump()

        else:
            return super().default(obj)

    @staticmethod
    def remove_null(obj):
        return {k: v for k, v in obj.items() if v is not None}


class Result(BaseModel):
    status: Literal["ok", "failed"] = "ok"
    code: int = 200
    retcode: int = 0
    msg: Optional[str] = None
    description: Optional[str] = None
    data: Any = None

    def to_http(self):
        result = self.model_dump(exclude={"code"}, exclude_none=True)
        return json(sys_json.dumps(result), self.code)

    def to_ws(self):
        result = self.model_dump(exclude={"code"}, exclude_none=True)
        return sys_json.dumps(result)
