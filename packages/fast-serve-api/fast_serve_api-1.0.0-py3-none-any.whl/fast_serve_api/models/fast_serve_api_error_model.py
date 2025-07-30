from .fast_serve_api_model import FastServeApiModel


class FastServeApiErrorModel(FastServeApiModel):
    status_code: int
    stack_trace: str
