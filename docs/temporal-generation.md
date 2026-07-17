# 关键帧与补帧接入

Box A 不直接操作 ComfyUI 节点，而是向 Box B 提交两个可选任务：

- `keyframe_sequence`：根据起止图、动作计划和参考图生成关键帧。
- `frame_interpolation`：将关键帧序列补到项目目标帧率。

Box B 应在 `/v1/capabilities` 声明 `keyframe_generation`、`interpolation_engines` 和 `controlnets`。Box A 根据声明选择 workflow；缺少补帧引擎时使用渲染器兜底，并在决策日志中记录。

## 推荐工作流 ID

```text
keyframe_sequence_v1
frame_interpolation_rife_v1
frame_interpolation_film_v1
```

真实 ComfyUI workflow JSON 应保存在 Box B 的 workflow 注册目录，不要把模型特定节点 JSON 写进 Skill。Box A 只提交 workflow ID 和有界参数：关键帧密度、IP-Adapter/OpenPose/Depth 权重、源帧率和目标帧率。

## 质量反馈格式

```json
{
  "identity_drift": 0.0,
  "motion_jump": 0.0,
  "rigidity": 0.0,
  "ghosting": 0.0,
  "action": "accept"
}
```

当任一指标超过 0.25 时，Box A 可调用 `RuntimePlanner.adjust_after_quality` 有界调整并重试，最多重试次数由 `config/config.yaml` 控制。
