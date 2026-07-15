from dataclasses import dataclass
from typing import Protocol


@dataclass
class GenerationResult:
    artifact_id: str
    uri: str
    provider: str
    metadata: dict[str, str]


class VideoProvider(Protocol):
    name: str

    def generate(self, prompt: str, duration_sec: float, aspect_ratio: str) -> GenerationResult:
        ...


class Renderer(Protocol):
    def render(self, project_id: str, shots: list[dict]) -> GenerationResult:
        ...

