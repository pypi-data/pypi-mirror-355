from __future__ import annotations
from ..types import Candidate, Result
from .base import EngineBase
from ..registry import register

@register
class PDFEngine(EngineBase):
    name = "pdf"
    cost = 0.1
    _MAGIC = b"%PDF" # in-house
    def sniff(self, payload: bytes) -> Result:
        window = payload[:8]#check first 8 bytes
        idx = window.find(self._MAGIC)
        cand = []
        if idx != -1:
            conf = 1.0 if idx == 0 else 0.90 - min(idx / (1 << 20), 0.1)
            cand.append(
                Candidate(
                    media_type="application/pdf",
                    extension="pdf",
                    confidence=conf,
                    breakdown={"offset": float(idx)},
                )
            )
        return Result(candidates=cand)
