import json
import time
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from typing import Any

from .capabilities import CapabilityRegistry, MediaCapabilities


class MediaBoxError(RuntimeError):
    pass


@dataclass
class MediaJob:
    job_id: str
    status: str
    payload: dict[str, Any]


class MediaBoxClient:
    """Small stdlib client for the Media Box contract (HTTP/JSON)."""

    def __init__(self, base_url: str, token: str | None = None, timeout_sec: float = 30):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout_sec = timeout_sec

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        data = json.dumps(body).encode() if body is not None else None
        headers = {"Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = Request(f"{self.base_url}{path}", data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self.timeout_sec) as response:
                return json.loads(response.read().decode())
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise MediaBoxError(f"Media Box request failed: {method} {path}: {exc}") from exc

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/v1/health")

    def capabilities(self) -> MediaCapabilities:
        return MediaCapabilities.from_dict(self._request("GET", "/v1/capabilities"))

    def refresh_registry(self, registry: CapabilityRegistry) -> MediaCapabilities:
        capabilities = self.capabilities()
        registry.current = capabilities
        return capabilities

    def submit_video(self, payload: dict[str, Any]) -> MediaJob:
        response = self._request("POST", "/v1/jobs/video", payload)
        return MediaJob(response["job_id"], response.get("status", "queued"), response)

    def get_job(self, job_id: str) -> MediaJob:
        response = self._request("GET", f"/v1/jobs/{job_id}")
        return MediaJob(job_id, response.get("status", "unknown"), response)

    def wait_for_job(self, job_id: str, poll_interval_sec: float = 2, max_wait_sec: float = 3600) -> MediaJob:
        deadline = time.monotonic() + max_wait_sec
        while time.monotonic() < deadline:
            job = self.get_job(job_id)
            if job.status in {"completed", "failed", "cancelled"}:
                return job
            time.sleep(poll_interval_sec)
        raise MediaBoxError(f"job timed out: {job_id}")

