from dataclasses import dataclass, asdict
from typing import Any

from ..models.project import VideoProject
from .capabilities import CapabilityRegistry


@dataclass
class ExecutionPlan:
    video_model: str
    shot_duration_sec: float
    resolution: str
    parallelism: int = 1
    fallback_model: str | None = None
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class RuntimePlanner:
    """Chooses a plan from live media-box capabilities without changing the Skill."""

    def make_plan(self, project: VideoProject, registry: CapabilityRegistry, quality: str = "normal") -> ExecutionPlan:
        model = registry.select_video(project.aspect_ratio, quality)
        fallback = next((m.model_id for m in registry.current.video_models if m.model_id != model.model_id), None)
        duration = min(4.0, model.max_duration_sec)
        reason = f"selected {model.model_id} from {registry.current.device_id}; max segment {model.max_duration_sec}s"
        if model.queue_length > 2:
            reason += "; queue is busy, use serial generation"
        return ExecutionPlan(model.model_id, duration, model.max_resolution, 1, fallback, reason)

