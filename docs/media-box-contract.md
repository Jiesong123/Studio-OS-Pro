# Media Box contract

Box A is the control/workflow plane. Box B is the media worker plane connected over the QSFP network link. Box A must not depend on a specific model implementation; it uses this small HTTP/JSON contract.

```text
GET  /v1/health
GET  /v1/capabilities
POST /v1/jobs/image
POST /v1/jobs/video
POST /v1/jobs/render
GET  /v1/jobs/{job_id}
GET  /v1/artifacts/{artifact_id}
```

`POST /v1/jobs/video` returns `{ "job_id": "...", "status": "queued" }`. A completed job returns an `artifacts` array containing at least `{ "artifact_id": "...", "uri": "..." }`.

The contract is intentionally independent of the local model runner. A Media Worker on Box B can adapt a Python script, a container, ComfyUI, or a remote provider without changing the Box A Skill.

For development, start the contract-compatible stub on Box B with:

```bash
PYTHONPATH=src python3 -m studio_os_video.media_box.worker
```

Replace `MediaWorkerState.submit_video` with the real local model or job-queue invocation when the Box B model entry point is known.
