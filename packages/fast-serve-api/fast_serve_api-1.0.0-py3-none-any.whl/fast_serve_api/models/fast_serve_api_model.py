from pydantic import BaseModel


class FastServeApiModel(BaseModel):
    success: bool
    message: str
    status_code: int | None = None
