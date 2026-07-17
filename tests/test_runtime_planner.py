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


def test_plan_selects_temporal_pipeline_and_bounded_retry_adjustment():
    registry = CapabilityRegistry(MediaCapabilities(
        device_id="media-box-01", status="ready",
        video_models=[VideoModelCapability("local-video")],
        keyframe_generation=True,
        interpolation_engines=["rife"],
        controlnets=["openpose", "depth"],
    ))
    pipeline = VideoPipeline(capabilities=registry)
    project = pipeline.create_project("两个角色激烈打斗", duration_sec=4)
    planned = pipeline.refresh_execution_plan(project.project_id)
    assert planned.runtime_plan["keyframes_per_sec"] == 8
    assert planned.runtime_plan["interpolation_workflow"] == "frame_interpolation_rife_v1"
    plan = pipeline.planner.make_plan(project, registry)
    adjusted = pipeline.planner.adjust_after_quality(plan, {"motion_jump": 0.5, "identity_drift": 0.4})
    assert adjusted.keyframes_per_sec == 10
    assert adjusted.parameters["ip_adapter_weight"] == 0.85
