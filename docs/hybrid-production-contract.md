# 混合视频生产交接契约

Studio OS 是剧情和分镜的单一真源。混合视频生产技能负责选择 T2I→I2V、T2V 或视频延长，调用已验证工作流并执行三帧验收。

## 必填镜头信息

人物动态镜头必须提供：

- `story.beat`、`story.emotion_start`、`story.emotion_end`
- `bindings.character_ids`、`bindings.wardrobe_ids`、`bindings.scene_id`
- `motion.start_state`、`motion.primary_action`、`motion.progression`、`motion.end_state`
- `camera.movement`、`camera.screen_direction`
- `continuity.kind`；连续镜头还要提供 `previous_shot_id`
- `production.mode`

一个约 5 秒镜头只安排一个主要动作和一个主要运镜。

## 连续性

`continuity.kind` 为 `continuous` 时，导出程序要求前一镜头已经出现在计划中，并把前一镜头的已验收尾帧作为当前镜头起始帧。`cut` 表示剪辑切换，不表示允许改变角色身份、服装、道具、场景、时间或天气。

未经剧本授权的变化不得写入提示词。允许变化写入 `continuity.authorized_changes`。

## 生成模式

- 固定人物、对白、手部、道具和连续动作：`t2i_i2v_keyframe`
- 承接上一段视频且存在已验证延长工作流：`video_extend`
- 无人物空镜、环境、抽象转场：`t2v`
- 包含固定人物的 T2V 必须提供 `production.reference_conditioning`

## 导出

```bash
python scripts/export_hybrid_plan.py project.json --output-dir production
```

输出：

```text
production/project-bible.json
production/shot-plan.json
```

当前混合生产合同 v1 使用统一的 `num_frames`；同一个计划中的镜头必须使用相同时长和 FPS。需要不同镜头时长时，拆分为多个生产计划。

导出只生成生产合同，不提交 ComfyUI。生产端必须继续验证工作流状态、媒体可下载性、视频解码以及第一/中间/最后帧。
