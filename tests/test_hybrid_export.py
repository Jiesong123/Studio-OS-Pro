import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "export_hybrid_plan.py"
SPEC = importlib.util.spec_from_file_location("export_hybrid_plan", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


def project_fixture():
    return {
        "schema_version": "1.2",
        "project_id": "flower_story",
        "aspect_ratio": "9:16",
        "runtime_plan": {"target_fps": 24},
        "series": {
            "characters": [
                {
                    "character_id": "boy_a",
                    "name": "男孩",
                    "visual_identity": {"wardrobes": {"boy_daily": {"anchor": "white shirt"}}},
                }
            ],
            "world": {"scenes": [{"scene_id": "flower_field", "name": "花田"}]},
        },
        "shots": [
            {
                "shot_id": "shot01",
                "index": 1,
                "duration_sec": 5,
                "story": {"beat": "男孩进入花田"},
                "bindings": {
                    "character_ids": ["boy_a"],
                    "wardrobe_ids": ["boy_daily"],
                    "prop_ids": [],
                    "scene_id": "flower_field",
                },
                "motion": {
                    "start_state": "站在小路入口",
                    "primary_action": "向前慢走",
                    "progression": "迈步后逐渐稳定",
                    "end_state": "走到花田中央",
                },
                "camera": {"movement": "平行跟拍", "screen_direction": "left_to_right"},
                "continuity": {"kind": "cut"},
                "production": {
                    "mode": "t2i_i2v_keyframe",
                    "workflow_ids": {"t2i": "flux2-v1", "motion": "ltx-kfi-v1"},
                },
            },
            {
                "shot_id": "shot02",
                "index": 2,
                "duration_sec": 5,
                "story": {"beat": "男孩加速"},
                "bindings": {
                    "character_ids": ["boy_a"],
                    "wardrobe_ids": ["boy_daily"],
                    "prop_ids": [],
                    "scene_id": "flower_field",
                },
                "motion": {
                    "start_state": "走到花田中央",
                    "primary_action": "从走路加速为轻跑",
                    "progression": "步幅逐渐增大",
                    "end_state": "保持稳定轻跑",
                },
                "camera": {"movement": "平行跟拍", "screen_direction": "left_to_right"},
                "continuity": {"kind": "continuous", "previous_shot_id": "shot01"},
                "production": {
                    "mode": "t2i_i2v_keyframe",
                    "workflow_ids": {"t2i": "flux2-v1", "motion": "ltx-kfi-v1"},
                },
            },
        ],
    }


def test_export_builds_bible_and_inherits_last_frame():
    bible, plan = MODULE.export_project(project_fixture())
    assert "boy_a" in bible["characters"]
    assert "flower_field" in bible["scenes"]
    shot02 = plan["shots"][1]
    assert shot02["continuity"]["inherited_start_frame"] == "qa/shot01/last_frame.png"
    assert shot02["keyframes"]["start"] == "qa/shot01/last_frame.png"
    assert shot02["num_frames"] == 121
    assert plan["technical"]["num_frames"] == 121


def test_export_rejects_missing_motion_state():
    project = project_fixture()
    project["shots"][0]["motion"]["progression"] = ""
    try:
        MODULE.export_project(project)
    except MODULE.ExportError as exc:
        assert "shot01.motion.progression is required" in str(exc)
    else:
        raise AssertionError("expected ExportError")


def test_export_rejects_unknown_wardrobe():
    project = project_fixture()
    project["shots"][0]["bindings"]["wardrobe_ids"] = ["missing_wardrobe"]
    try:
        MODULE.export_project(project)
    except MODULE.ExportError as exc:
        assert "unknown wardrobe_id missing_wardrobe" in str(exc)
    else:
        raise AssertionError("expected ExportError")
