from uuid import uuid4

from .base import GenerationResult


class MockVideoProvider:
    """Deterministic provider for local development and integration tests."""

    name = "mock-video"

    def generate(self, prompt: str, duration_sec: float, aspect_ratio: str) -> GenerationResult:
        artifact_id = f"mock_{uuid4().hex[:8]}"
        return GenerationResult(
            artifact_id=artifact_id,
            uri=f"mock://video/{artifact_id}",
            provider=self.name,
            metadata={"prompt": prompt, "duration_sec": str(duration_sec), "aspect_ratio": aspect_ratio},
        )


class MockRenderer:
    name = "mock-renderer"

    def render(self, project_id: str, shots: list[dict]) -> GenerationResult:
        artifact_id = f"render_{uuid4().hex[:8]}"
        return GenerationResult(
            artifact_id=artifact_id,
            uri=f"mock://render/{project_id}/{artifact_id}.mp4",
            provider=self.name,
            metadata={"shot_count": str(len(shots))},
        )

