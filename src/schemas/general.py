from pydantic import BaseModel, model_validator
from typing import Generic, TypeVar, List, Optional


T = TypeVar("T", bound=BaseModel)


class Pagination(BaseModel, Generic[T]):

    total: int
    limit: int
    offset: int
    page: Optional[int] = None
    pages: Optional[int] = None
    results: List[T]

    @model_validator(mode="after")
    def compute_pages(self):
        self.page = (self.offset // self.limit) + 1
        self.pages = (self.total + self.limit - 1) // self.limit
        return self


class IntId(BaseModel):

    id: int