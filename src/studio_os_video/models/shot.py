from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Shot:
    """A regeneratable unit of a video timeline."""

    shot_id: str
    index: int
    duration_sec: float
    purpose: str
    visual_prompt: str = ""
    narration: str | None = None
    subtitle: str | None = None
    story: dict[str, Any] = field(default_factory=dict)
    bindings: dict[str, Any] = field(default_factory=dict)
    motion: dict[str, Any] = field(default_factory=dict)
    camera: dict[str, Any] = field(default_factory=dict)
    continuity: dict[str, Any] = field(default_factory=dict)
    production: dict[str, Any] = field(default_factory=dict)
    qa: dict[str, Any] = field(default_factory=dict)
    assets: list[str] = field(default_factory=list)
    status: str = "planned"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
