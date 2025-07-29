from __future__ import annotations
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict

class Candidate(BaseModel):
    media_type: str
    extension: Optional[str] = None
    confidence: float = Field(ge=0, le=1)
    breakdown: Dict[str, float] | None = None

class Result(BaseModel):
    """Unified return object for every engine.

    Engines can populate only *candidates*; framework fills the rest.
    """
    engine: str = ""
    bytes_analyzed: int = 0         
    elapsed_ms: float = 0.0
    candidates: List[Candidate]
    error: str | None = None
    hash: str | None = None

BaseModel.model_config = ConfigDict(extra="forbid", populate_by_name=True)
