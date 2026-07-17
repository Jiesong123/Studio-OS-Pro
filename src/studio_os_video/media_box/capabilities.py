from dataclasses import dataclass, field
from typing import Any


@dataclass
class VideoModelCapability:
    model_id: str
    max_duration_sec: float = 4
    max_resolution: str = "768p"
    supported_ratios: list[str] = field(default_factory=lambda: ["9:16", "16:9", "1:1"])
    queue_length: int = 0
    kind: str = "local"

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "VideoModelCapability":
        return cls(
            model_id=value.get("model_id", value.get("id", "unknown")),
            max_duration_sec=float(value.get("max_duration_sec", 4)),
            max_resolution=value.get("max_resolution", "768p"),
            supported_ratios=value.get("supported_ratios", ["9:16", "16:9", "1:1"]),
            queue_length=int(value.get("queue_length", 0)),
            kind=value.get("type", value.get("kind", "local")),
        )


@dataclass
class MediaCapabilities:
    device_id: str
    status: str
    video_models: list[VideoModelCapability] = field(default_factory=list)
    image_models: list[dict[str, Any]] = field(default_factory=list)
    renderers: list[str] = field(default_factory=list)
    resources: dict[str, Any] = field(default_factory=dict)
    keyframe_generation: bool = False
    interpolation_engines: list[str] = field(default_factory=list)
    controlnets: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "MediaCapabilities":
        groups = value.get("capabilities", value)
        videos = groups.get("video_generation", groups.get("video_models", []))
        images = groups.get("image_generation", groups.get("image_models", []))
        return cls(
            device_id=value.get("device_id", "media-box"),
            status=value.get("status", "unknown"),
            video_models=[VideoModelCapability.from_dict(item) for item in videos],
            image_models=images,
            renderers=groups.get("rendering", groups.get("renderers", [])),
            resources=value.get("resources", {}),
            keyframe_generation=bool(groups.get("keyframe_generation", False)),
            interpolation_engines=groups.get("interpolation_engines", []),
            controlnets=groups.get("controlnets", []),
        )


class CapabilityRegistry:
    """Runtime cache of the media box capabilities."""

    def __init__(self, capabilities: MediaCapabilities | None = None):
        self.current = capabilities or MediaCapabilities("unknown", "unknown")

    def update(self, payload: dict[str, Any]) -> MediaCapabilities:
        self.current = MediaCapabilities.from_dict(payload)
        return self.current

    def select_video(self, aspect_ratio: str, quality: str = "normal") -> VideoModelCapability:
        candidates = [m for m in self.current.video_models if aspect_ratio in m.supported_ratios]
        if not candidates:
            candidates = self.current.video_models
        if not candidates:
            raise LookupError("media box has no compatible video model")
        if quality == "high":
            return sorted(candidates, key=lambda m: (m.max_resolution, -m.queue_length), reverse=True)[0]
        return sorted(candidates, key=lambda m: (m.queue_length, m.kind != "local"))[0]
