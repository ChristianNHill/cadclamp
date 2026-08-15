from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

PASS = "pass"
WARN = "warn"
FAIL = "fail"
SKIPPED = "skipped"


@dataclass
class GateResult:
    gate: str
    status: str  # pass | fail | skipped
    code: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class CheckResult:
    check: str
    index: float  # 0..1, higher is better
    band: str  # pass | warn | fail
    measured: dict[str, Any] = field(default_factory=dict)
    thresholds: dict[str, Any] = field(default_factory=dict)
    convention: str = ""


@dataclass
class ReportCard:
    part: str
    engine_version: str
    process: dict[str, Any]
    gates: list[GateResult] = field(default_factory=list)
    checks: list[CheckResult] = field(default_factory=list)
    printability: float | None = None
    failure_code: str | None = None

    @property
    def gated_out(self) -> bool:
        return self.failure_code is not None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self, **kwargs: Any) -> str:
        return json.dumps(self.to_dict(), **kwargs)
