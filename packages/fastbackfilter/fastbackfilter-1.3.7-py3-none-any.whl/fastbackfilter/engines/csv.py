from __future__ import annotations

from ..types import Candidate, Result
from .base import EngineBase
from ..registry import register

@register
class CSVEngine(EngineBase):
    name = "csv"
    cost = 0.05

    def sniff(self, payload: bytes) -> Result:
        sample = payload.splitlines()[:2]
        if sample and any(b"," in line for line in sample):
            cand = Candidate(media_type="text/csv", extension="csv", confidence=0.90)
            return Result(candidates=[cand])
        return Result(candidates=[])
