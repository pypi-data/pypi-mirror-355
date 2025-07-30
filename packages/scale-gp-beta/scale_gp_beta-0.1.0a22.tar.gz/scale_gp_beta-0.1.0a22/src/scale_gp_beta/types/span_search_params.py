# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union
from datetime import datetime
from typing_extensions import Literal, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["SpanSearchParams"]


class SpanSearchParams(TypedDict, total=False):
    ending_before: str

    from_ts: Annotated[Union[str, datetime], PropertyInfo(format="iso8601")]
    """The starting (oldest) timestamp in ISO format."""

    limit: int

    sort_order: Literal["asc", "desc"]

    starting_after: str

    to_ts: Annotated[Union[str, datetime], PropertyInfo(format="iso8601")]
    """The ending (most recent) timestamp in ISO format."""

    extra_metadata: Dict[str, object]
    """Filter on custom metadata key-value pairs"""

    group_id: str
    """Filter by group ID"""

    name: str
    """Filter by trace/span name"""

    parents_only: bool
    """Only fetch spans that are the top-level (ie. have no parent_id)"""

    span_id: str
    """Filter by span ID"""

    status: Literal["SUCCESS", "ERROR"]
    """Filter on span status"""

    trace_id: str
    """Which trace_id to filter on"""

    type: Literal[
        "TEXT_INPUT",
        "TEXT_OUTPUT",
        "COMPLETION_INPUT",
        "COMPLETION",
        "KB_RETRIEVAL",
        "KB_INPUT",
        "RERANKING",
        "EXTERNAL_ENDPOINT",
        "PROMPT_ENGINEERING",
        "DOCUMENT_INPUT",
        "MAP_REDUCE",
        "DOCUMENT_SEARCH",
        "DOCUMENT_PROMPT",
        "CUSTOM",
        "INPUT_GUARDRAIL",
        "OUTPUT_GUARDRAIL",
        "CODE_EXECUTION",
        "DATA_MANIPULATION",
        "EVALUATION",
        "FILE_RETRIEVAL",
        "KB_ADD_CHUNK",
        "KB_MANAGEMENT",
        "TRACER",
        "AGENT_TRACER",
        "AGENT_WORKFLOW",
        "STANDALONE",
    ]
