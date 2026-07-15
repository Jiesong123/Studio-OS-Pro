"""Development Media Worker implementing the Box B HTTP contract.

Replace `_run_video_job` with the Box B local model invocation in production.
"""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from uuid import uuid4


class MediaWorkerState:
    def __init__(self) -> None:
        self.jobs: dict[str, dict[str, Any]] = {}

    def capabilities(self) -> dict[str, Any]:
        return {
            "device_id": "media-box-dev",
            "status": "ready",
            "capabilities": {
                "image_generation": [{"model_id": "local-image-dev"}],
                "video_generation": [{
                    "model_id": "local-video-dev",
                    "max_duration_sec": 4,
                    "max_resolution": "768p",
                    "supported_ratios": ["9:16", "16:9", "1:1"],
                    "queue_length": 0,
                    "type": "local",
                }],
                "rendering": ["ffmpeg"],
            },
            "resources": {"queue_length": 0},
        }

    def submit_video(self, payload: dict[str, Any]) -> dict[str, Any]:
        job_id = f"job_{uuid4().hex[:10]}"
        artifact_id = f"artifact_{uuid4().hex[:10]}"
        # Development mode completes immediately. Production should enqueue the local model.
        self.jobs[job_id] = {
            "job_id": job_id,
            "status": "completed",
            "request": payload,
            "artifacts": [{
                "artifact_id": artifact_id,
                "kind": "video",
                "mime_type": "video/mp4",
                "uri": f"media://{artifact_id}",
            }],
        }
        return {"job_id": job_id, "status": "completed"}


def make_handler(state: MediaWorkerState):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, status: int, value: dict[str, Any]) -> None:
            data = json.dumps(value).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:
            if self.path == "/v1/health":
                self._send(200, {"status": "ok", "device_id": "media-box-dev"})
            elif self.path == "/v1/capabilities":
                self._send(200, state.capabilities())
            elif self.path.startswith("/v1/jobs/"):
                job_id = self.path.rsplit("/", 1)[-1]
                job = state.jobs.get(job_id)
                self._send(200, job) if job else self._send(404, {"error": "job_not_found"})
            else:
                self._send(404, {"error": "not_found"})

        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            try:
                payload = json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError:
                self._send(400, {"error": "invalid_json"})
                return
            if self.path == "/v1/jobs/video":
                self._send(202, state.submit_video(payload))
            else:
                self._send(404, {"error": "not_found"})

        def log_message(self, format: str, *args: Any) -> None:
            return

    return Handler


def run(host: str = "0.0.0.0", port: int = 9000) -> None:
    server = ThreadingHTTPServer((host, port), make_handler(MediaWorkerState()))
    print(f"Media Worker listening on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()

