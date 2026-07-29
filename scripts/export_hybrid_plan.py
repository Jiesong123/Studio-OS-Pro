#!/usr/bin/env python3
"""Export a Studio OS project to hybrid video production contracts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ALLOWED_MODES = {"t2i_i2v_keyframe", "t2v", "video_extend"}


class ExportError(ValueError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ExportError("project root must be an object")
    return value


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def require_text(value: Any, field: str, errors: list[str]) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    errors.append(f"{field} is required")
    return ""


def keyed(values: Any, id_fields: tuple[str, ...]) -> dict[str, Any]:
    if isinstance(values, dict):
        return values
    result = {}
    for item in as_list(values):
        if not isinstance(item, dict):
            continue
        item_id = next((item.get(name) for name in id_fields if item.get(name)), None)
        if item_id:
            result[str(item_id)] = item
    return result


def build_project_bible(project: dict[str, Any]) -> dict[str, Any]:
    explicit = as_dict(project.get("project_bible")) or as_dict(
        as_dict(project.get("script")).get("project_bible")
    )
    if explicit:
        return explicit

    series = as_dict(project.get("series"))
    world = as_dict(series.get("world"))
    script = as_dict(project.get("script"))
    characters = keyed(series.get("characters"), ("character_id", "id"))
    for character in characters.values():
        visual = as_dict(character.get("visual_identity"))
        character.setdefault("immutable_anchor", visual.get("prompt_anchor", visual.get("description", "")))
        character.setdefault("wardrobes", as_dict(visual.get("wardrobes")))

    return {
        "schema_version": 1,
        "project_id": project.get("project_id", ""),
        "style": script.get("visual_style", world.get("visual_style", {})),
        "characters": characters,
        "props": keyed(script.get("props", world.get("props", {})), ("prop_id", "id")),
        "scenes": keyed(script.get("scenes", world.get("scenes", {})), ("scene_id", "id")),
        "world": world,
    }


def default_num_frames(duration_sec: float, fps: float) -> int:
    approximate = max(9, round(duration_sec * fps))
    return max(9, round((approximate - 1) / 8) * 8 + 1)


def export_shot(
    shot: dict[str, Any],
    previous_ids: set[str],
    fps: float,
    errors: list[str],
) -> dict[str, Any]:
    shot_id = require_text(shot.get("shot_id"), "shot.shot_id", errors)
    prefix = shot_id or "shot"
    story = as_dict(shot.get("story"))
    bindings = as_dict(shot.get("bindings"))
    motion = as_dict(shot.get("motion"))
    camera = as_dict(shot.get("camera"))
    continuity = as_dict(shot.get("continuity"))
    production = as_dict(shot.get("production"))
    mode = production.get("mode")

    require_text(story.get("beat"), f"{prefix}.story.beat", errors)
    require_text(bindings.get("scene_id"), f"{prefix}.bindings.scene_id", errors)
    require_text(motion.get("start_state"), f"{prefix}.motion.start_state", errors)
    require_text(motion.get("primary_action"), f"{prefix}.motion.primary_action", errors)
    require_text(motion.get("progression"), f"{prefix}.motion.progression", errors)
    require_text(motion.get("end_state"), f"{prefix}.motion.end_state", errors)
    require_text(camera.get("movement"), f"{prefix}.camera.movement", errors)
    require_text(camera.get("screen_direction"), f"{prefix}.camera.screen_direction", errors)
    if mode not in ALLOWED_MODES:
        errors.append(f"{prefix}.production.mode must be one of {sorted(ALLOWED_MODES)}")

    previous_id = continuity.get("previous_shot_id")
    kind = continuity.get("kind", "cut")
    inherited = continuity.get("inherited_start_frame")
    if kind == "continuous":
        if not previous_id:
            errors.append(f"{prefix}.continuity.previous_shot_id is required for continuous shots")
        elif previous_id not in previous_ids:
            errors.append(f"{prefix}.continuity.previous_shot_id must reference an earlier shot")
        inherited = inherited or f"qa/{previous_id}/last_frame.png"

    character_ids = as_list(bindings.get("character_ids"))
    reference_conditioning = as_dict(production.get("reference_conditioning"))
    if mode == "t2v" and character_ids:
        if not reference_conditioning.get("validated_workflow_id") or not reference_conditioning.get("reference_files"):
            errors.append(f"{prefix}: T2V with characters requires validated reference conditioning")

    keyframes = as_dict(production.get("keyframes"))
    workflow_ids = as_dict(production.get("workflow_ids"))
    if mode == "t2i_i2v_keyframe":
        keyframes.setdefault("start", inherited or f"keyframes/{shot_id}/start.png")
        keyframes.setdefault("end", f"keyframes/{shot_id}/end.png")
        if not workflow_ids.get("t2i") or not workflow_ids.get("motion"):
            errors.append(f"{prefix}: T2I/I2V requires t2i and motion workflow IDs")
    if mode == "video_extend" and not workflow_ids.get("motion"):
        errors.append(f"{prefix}: video_extend requires a motion workflow ID")

    duration = float(shot.get("duration_sec", 0) or 0)
    qa = as_dict(shot.get("qa"))
    return {
        "shot_id": shot_id,
        "index": shot.get("index"),
        "duration_sec": duration,
        "story": story,
        "mode": mode,
        "character_ids": character_ids,
        "wardrobe_ids": as_list(bindings.get("wardrobe_ids")),
        "prop_ids": as_list(bindings.get("prop_ids")),
        "scene_id": bindings.get("scene_id"),
        "motion": motion,
        "camera": camera,
        "continuity": {
            "kind": kind,
            "previous_shot_id": previous_id,
            "inherited_start_frame": inherited,
            "authorized_changes": as_list(continuity.get("authorized_changes")),
        },
        "keyframes": keyframes,
        "workflow_ids": workflow_ids,
        "reference_conditioning": reference_conditioning,
        "qa": {
            "first_frame": qa.get("first_frame"),
            "middle_frame": qa.get("middle_frame"),
            "last_frame": qa.get("last_frame"),
            "passed": bool(qa.get("passed", False)),
        },
        "num_frames": default_num_frames(duration, fps),
        "visual_prompt": shot.get("visual_prompt", ""),
    }


def export_project(project: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    errors: list[str] = []
    shots = as_list(project.get("shots"))
    if not shots:
        raise ExportError("project.shots must contain at least one shot")

    runtime = as_dict(project.get("runtime_plan"))
    fps = float(runtime.get("target_fps", runtime.get("fps", 24)) or 24)
    output_shots = []
    previous_ids: set[str] = set()
    for index, shot in enumerate(shots):
        if not isinstance(shot, dict):
            errors.append(f"shots[{index}] must be an object")
            continue
        exported = export_shot(shot, previous_ids, fps, errors)
        if exported["shot_id"] in previous_ids:
            errors.append(f"{exported['shot_id']}: duplicate shot_id")
        previous_ids.add(exported["shot_id"])
        output_shots.append(exported)

    bible = build_project_bible(project)
    known_wardrobes = {
        wardrobe_id
        for character in bible.get("characters", {}).values()
        if isinstance(character, dict)
        for wardrobe_id in as_dict(character.get("wardrobes"))
    }
    for shot in output_shots:
        prefix = shot["shot_id"]
        for character_id in shot["character_ids"]:
            if character_id not in bible.get("characters", {}):
                errors.append(f"{prefix}: unknown character_id {character_id}")
        for prop_id in shot["prop_ids"]:
            if prop_id not in bible.get("props", {}):
                errors.append(f"{prefix}: unknown prop_id {prop_id}")
        for wardrobe_id in shot["wardrobe_ids"]:
            if wardrobe_id not in known_wardrobes:
                errors.append(f"{prefix}: unknown wardrobe_id {wardrobe_id}")
        if shot["scene_id"] not in bible.get("scenes", {}):
            errors.append(f"{prefix}: unknown scene_id {shot['scene_id']}")

    frame_counts = {shot["num_frames"] for shot in output_shots}
    if len(frame_counts) > 1:
        errors.append(
            "hybrid production v1 requires one shared num_frames value; "
            "split shots with different durations into separate plans"
        )

    if errors:
        raise ExportError("\n".join(errors))

    num_frames = next(iter(frame_counts))
    plan = {
        "schema_version": 1,
        "project_id": project.get("project_id", ""),
        "source_schema_version": project.get("schema_version", "1.0"),
        "technical": {
            "fps": fps,
            "num_frames": num_frames,
            "aspect_ratio": project.get("aspect_ratio", "9:16"),
        },
        "shots": output_shots,
    }
    return bible, plan


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    try:
        bible, plan = export_project(load_json(args.project))
    except (OSError, json.JSONDecodeError, ExportError) as exc:
        parser.error(str(exc))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.output_dir / "project-bible.json", bible)
    write_json(args.output_dir / "shot-plan.json", plan)
    print(f"exported {len(plan['shots'])} shots to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
