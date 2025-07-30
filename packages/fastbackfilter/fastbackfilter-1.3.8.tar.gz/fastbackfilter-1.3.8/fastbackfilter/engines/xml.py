from __future__ import annotations
from ..types import Candidate, Result
from .base import EngineBase
from ..registry import register

@register
class XMLEngine(EngineBase):
    name = "xml"
    _MAGIC = [b'\xEF\xBB\xBF', b'\xFF\xFE', b'\xFE\xFF', b"<?xml"]

    def sniff(self, payload: bytes) -> Result:
        window = payload[:8]
        cand = []

        for magic in self._MAGIC:
            idx = window.find(magic)
            if idx != -1:
                conf = 1.0 if idx == 0 else 0.90 - min(idx / (1 << 20), 0.1)
                cand.append(
                    Candidate(
                        media_type="application/xml",
                        extension="xml",
                        confidence=conf,
                    )
                )
                # Found a match, no need to check further
                break

        return Result(candidates=cand)
