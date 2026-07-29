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
    target_fps: int = 30
    keyframes_per_sec: int = 4
    source_fps: int = 8
    keyframe_workflow: str | None = None
    interpolation_workflow: str | None = None
    controlnet_modes: list[str] | None = None
    parameters: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class RuntimePlanner:
    """Chooses a plan from live media-box capabilities without changing the Skill."""

    def make_plan(self, project: VideoProject, registry: CapabilityRegistry, quality: str = "normal") -> ExecutionPlan:
        model = registry.select_video(project.aspect_ratio, quality)
        fallback = next((m.model_id for m in registry.current.video_models if m.model_id != model.model_id), None)
        duration = min(4.0, model.max_duration_sec)
        action_text = f"{project.prompt} {project.mode}".lower()
        fast = any(word in action_text for word in ("打斗", "战斗", "奔跑", "爆炸", "fight", "action"))
        static = any(word in action_text for word in ("静止", "产品展示", "说话", "portrait"))
        keyframes = 8 if fast else 2 if static else 4
        available = set(registry.current.controlnets)
        modes = [m for m in ("openpose", "depth") if m in available][:2]
        interpolation = registry.current.interpolation_engines
        interp_engine = interpolation[0] if interpolation else None
        reason = f"selected {model.model_id} from {registry.current.device_id}; max segment {model.max_duration_sec}s"
        if keyframes == 8:
            reason += "; fast-action density"
        if not interp_engine:
            reason += "; no live interpolation engine, use fallback"
        if model.queue_length > 2:
            reason += "; queue is busy, use serial generation"
        return ExecutionPlan(
            model.model_id, duration, model.max_resolution, 1, fallback, reason,
            target_fps=30, keyframes_per_sec=keyframes, source_fps=min(10, keyframes),
            keyframe_workflow="keyframe_sequence_v1" if registry.current.keyframe_generation else None,
            interpolation_workflow=f"frame_interpolation_{interp_engine}_v1" if interp_engine else None,
            controlnet_modes=modes,
            parameters={"ip_adapter_weight": 0.80, "openpose_weight": 0.85, "depth_weight": 0.55},
        )

    def adjust_after_quality(self, plan: ExecutionPlan, feedback: dict[str, Any]) -> ExecutionPlan:
        """Apply bounded, deterministic changes after a failed shot quality gate."""
        params = dict(plan.parameters or {})
        if feedback.get("identity_drift", 0) > 0.2:
            params["ip_adapter_weight"] = round(
                min(0.90, params.get("ip_adapter_weight", 0.80) + 0.05), 2
            )
        if feedback.get("motion_jump", 0) > 0.25:
            plan.keyframes_per_sec = min(10, plan.keyframes_per_sec + 2)
            plan.source_fps = min(10, plan.source_fps + 2)
        if feedback.get("rigidity", 0) > 0.25:
            params["openpose_weight"] = max(0.60, params.get("openpose_weight", 0.85) - 0.07)
            params["depth_weight"] = max(0.30, params.get("depth_weight", 0.55) - 0.05)
        if feedback.get("ghosting", 0) > 0.25:
            plan.keyframes_per_sec = min(10, plan.keyframes_per_sec + 2)
            plan.source_fps = min(10, plan.source_fps + 2)
        plan.parameters = params
        plan.reason = f"{plan.reason}; adjusted from quality feedback"
        return plan
