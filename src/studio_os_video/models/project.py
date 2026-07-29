from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

from .shot import Shot


class ProjectStatus(StrEnum):
    CREATED = "created"
    SCRIPT_READY = "script_ready"
    STORYBOARD_READY = "storyboard_ready"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class VideoProject:
    project_id: str
    prompt: str
    aspect_ratio: str = "9:16"
    duration_sec: int = 30
    language: str = "zh-CN"
    platform: str | None = None
    status: ProjectStatus = ProjectStatus.CREATED
    script: dict[str, Any] = field(default_factory=dict)
    shots: list[Shot] = field(default_factory=list)
    assets: list[dict[str, Any]] = field(default_factory=list)
    renders: list[dict[str, Any]] = field(default_factory=list)
    audio_tracks: list[dict[str, Any]] = field(default_factory=list)
    subtitles: list[dict[str, Any]] = field(default_factory=list)
    timeline: dict[str, Any] = field(default_factory=dict)
    runtime_plan: dict[str, Any] = field(default_factory=dict)
    decision_log: list[dict[str, Any]] = field(default_factory=list)
    mode: str = "short_video"
    series: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    schema_version: str = "1.2"
    version: int = 1
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def create(cls, prompt: str, **kwargs: Any) -> "VideoProject":
        return cls(project_id=f"vid_{uuid4().hex[:10]}", prompt=prompt, **kwargs)

    def touch(self) -> None:
        self.version += 1
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        return value
