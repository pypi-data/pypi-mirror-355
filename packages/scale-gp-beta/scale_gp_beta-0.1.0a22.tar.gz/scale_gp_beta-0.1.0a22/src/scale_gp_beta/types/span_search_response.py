# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from typing_extensions import Literal

from .span import Span
from .._models import BaseModel

__all__ = ["SpanSearchResponse"]


class SpanSearchResponse(BaseModel):
    has_more: bool
    """Whether there are more items left to be fetched."""

    items: List[Span]

    total: int
    """The total of items that match the query.

    This is greater than or equal to the number of items returned.
    """

    limit: Optional[int] = None
    """The maximum number of items to return."""

    object: Optional[Literal["list"]] = None
