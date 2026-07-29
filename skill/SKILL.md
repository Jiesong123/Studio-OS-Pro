---
name: video-creation
description: 兼容入口，用于连接 video-router 以及 product-video、short-drama、manhua-drama 专业 Skill。
---

# Video Creation

所有创建或修改视频的请求都在 Box A 使用 Studio OS Video Runtime。新任务先路由到 `video-router`，再使用 `product-video`、`short-drama` 或 `manhua-drama`。Box A 负责编排，Media Box（Box B）通过配置好的链路执行媒体推理和渲染。

## 工作流

1. 提取平台、画幅、时长、语言、受众、风格和行动召唤。只询问会实质影响结果的缺失选项。
2. 创建或恢复 `VideoProject`，在各步骤中始终保留项目 ID。
3. 选择模型前刷新 Media Box 能力注册表，根据实时的时长、画幅、队列和分辨率限制调整执行计划。
4. 规划脚本，再创建镜头表。每个镜头都应可独立重新生成。
5. 根据创作类型、视觉语言和平台，读取 `knowledge/` 下相关知识。
6. 只生成缺失素材，保留已确认素材和连续性参考。
7. 渲染预览，检查时长、画幅和字幕位置，并报告 artifact URI。
8. 修改时只处理受影响的镜头或时间线片段，再次渲染。

涉及动作连续性时，先读取 `../knowledge/common/temporal-pipeline.md`。Box A 负责按镜头规划关键帧密度和有界重试；Box B 负责执行实际的 ComfyUI/模型 workflow。不要把 30fps 等同于每秒生成 30 张独立图片。

需要交给 T2I→I2V、T2V 或视频延长生产技能时，为每个镜头填写 `story`、`bindings`、`motion`、`camera`、`continuity`、`production` 和 `qa`。运行 `python scripts/export_hybrid_plan.py <project.json> --output-dir <目录>`；只有导出校验通过，才提交媒体生产。字段和交接规则见 `../docs/hybrid-production-contract.md`。

## 模式路由

- 一次性信息、商业或社交视频使用 `short_video`。
- 出现重复角色、分集、连续剧情，或明确提出漫剧/短剧时使用 `drama`。读取 [workflows/drama.md](workflows/drama.md) 以及 `../knowledge/drama/` 下相关文件。
- `drama` 模式下，生成动态镜头前先创建剧集、角色卡、分集目标和连续性状态。使用 `VideoPipeline.create_drama_project`，并保持分集和镜头 ID 稳定。

## Runtime 契约

使用 `VideoPipeline.create_project`、`plan`、`storyboard`、`generate_assets` 和 `render`。Provider 可以替换，不要在 Skill 中写死供应商。

## 部署后检查

拉取新版本后，先运行 `PYTHONPATH=src python3 scripts/restart_advisor.py --base <上一版本提交号>`，读取 `config/restart-policy.json` 给出的建议。Runtime 或 Media Worker 代码变化时分别重启 Box A 或 Box B Worker；只改 Skill/知识库时重新加载上下文即可。该脚本只提供建议，不自动杀进程或重启服务。

## 质量门

- 镜头时长总和与目标时长的误差应在允许范围内。
- 每个镜头都有画面提示词和连续性参考。
- 最终渲染前，旁白和字幕必须同步。
- Provider 调用失败必须记录并支持重试。
- 完成结果必须包含可播放的渲染 URI 和项目 ID。
- `drama` 模式下，每集必须有目标、冲突、变化后的局面和悬念；每个重复角色必须有视觉参考和连续性记录。
- 动态人物镜头必须记录开始状态、单一主要动作、动作发展和结束状态。
- 连续镜头必须引用前一镜头，并继承已验收的最后一帧；明确切镜时仍须保持身份、服装、道具和场景锚点。

字段详细定义见 [references/project-model.md](references/project-model.md)。创作指导请读取 `../knowledge/` 下对应文件。
