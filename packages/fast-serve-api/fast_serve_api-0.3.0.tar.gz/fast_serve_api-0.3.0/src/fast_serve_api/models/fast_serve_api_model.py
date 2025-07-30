from typing import Optional

from pydantic import BaseModel


class FastServeApiModel(BaseModel):
    success: bool
    message: str
    status_code: Optional[int] = None
