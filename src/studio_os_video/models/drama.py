from dataclasses import asdict, dataclass, field
from typing import Any
from uuid import uuid4


@dataclass
class Character:
    character_id: str
    name: str
    role: str = "supporting"
    personality: list[str] = field(default_factory=list)
    visual_identity: dict[str, Any] = field(default_factory=dict)
    reference_assets: list[str] = field(default_factory=list)

    @classmethod
    def create(cls, name: str, role: str = "supporting", **kwargs: Any) -> "Character":
        return cls(f"char_{uuid4().hex[:8]}", name, role, **kwargs)


@dataclass
class Episode:
    episode_id: str
    index: int
    title: str
    objective: str = ""
    conflict: str = ""
    cliffhanger: str = ""
    status: str = "planned"
    shots: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class DramaSeries:
    series_id: str
    title: str
    genre: str
    episode_count: int = 1
    episode_duration_sec: int = 90
    world: dict[str, Any] = field(default_factory=dict)
    characters: list[Character] = field(default_factory=list)
    episodes: list[Episode] = field(default_factory=list)

    @classmethod
    def create(cls, title: str, genre: str, **kwargs: Any) -> "DramaSeries":
        return cls(f"series_{uuid4().hex[:8]}", title, genre, **kwargs)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

