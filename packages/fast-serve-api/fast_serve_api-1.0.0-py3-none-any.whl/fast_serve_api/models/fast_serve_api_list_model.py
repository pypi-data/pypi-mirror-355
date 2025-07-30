from .fast_serve_api_model import FastServeApiModel


class FastServeApiListModel(FastServeApiModel):
    page: int
    size: int
    last_page: bool
    total: int | None = None
