from ..media_box.client import MediaBoxClient
from .base import GenerationResult


class MediaBoxVideoProvider:
    """Video provider backed by the remote media box contract."""

    name = "media-box-video"

    def __init__(self, client: MediaBoxClient, model_id: str):
        self.client = client
        self.model_id = model_id

    def generate(self, prompt: str, duration_sec: float, aspect_ratio: str) -> GenerationResult:
        job = self.client.submit_video({
            "model_id": self.model_id,
            "prompt": prompt,
            "duration_sec": duration_sec,
            "aspect_ratio": aspect_ratio,
        })
        finished = self.client.wait_for_job(job.job_id)
        if finished.status != "completed":
            raise RuntimeError(f"media box video job failed: {job.job_id}")
        artifacts = finished.payload.get("artifacts", [])
        if not artifacts:
            raise RuntimeError(f"media box job has no artifacts: {job.job_id}")
        artifact = artifacts[0]
        return GenerationResult(
            artifact_id=artifact.get("artifact_id", job.job_id),
            uri=artifact["uri"],
            provider=self.name,
            metadata={"job_id": job.job_id, "model_id": self.model_id},
        )

