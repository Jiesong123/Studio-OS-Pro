from studio_os_video import VideoPipeline
from studio_os_video.media_box.capabilities import CapabilityRegistry, MediaCapabilities, VideoModelCapability


def test_box_a_adapts_plan_to_live_box_b_capabilities():
    registry = CapabilityRegistry(MediaCapabilities(
        device_id="media-box-01",
        status="ready",
        video_models=[
            VideoModelCapability("local-video", max_duration_sec=4, max_resolution="768p", queue_length=0),
            VideoModelCapability("remote-video", max_duration_sec=8, max_resolution="1080p", queue_length=4, kind="remote"),
        ],
    ))
    pipeline = VideoPipeline(capabilities=registry)
    project = pipeline.create_project("产品视频", duration_sec=30)
    planned = pipeline.refresh_execution_plan(project.project_id, quality="normal")
    assert planned.runtime_plan["video_model"] == "local-video"
    assert planned.runtime_plan["shot_duration_sec"] == 4
    assert planned.decision_log

