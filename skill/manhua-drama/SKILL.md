---
name: manhua-drama
description: 创建动态漫画、漫剧、动漫分格和插画式连续视频，保持角色、分格构图、表情以及图生视频的连续性。
---

# 漫剧

用于动态漫画、漫剧、插画短剧和分格叙事。读取 `knowledge/common/`、`knowledge/drama/`、`knowledge/manhua/` 和平台规则。

工作流：确定视觉风格和分格语言 → 创建角色设定表与表情库 → 规划故事节拍和画格 → 生成并确认参考图 → 将动作拆成镜头和关键帧 → 使用变化的 OpenPose、Depth 或 Lineart 控制生成过渡 → 制作画格动画或图生视频镜头 → 生成对白、旁白、字幕和音乐计划 → 保持人物、服装、道具和画风一致 → 检查画格可读性、运动连续性、音频和转场 → 渲染。

每个动态镜头必须填写：剧情节拍与情绪变化、角色/服装/道具/场景 ID、开始状态、单一主要动作、动作发展、结束状态、屏幕方向、镜头运动和承接方式。不要只写最终画面提示词。

对于打斗等复杂动作，先读取 `knowledge/manhua/action-sequence.md` 和 `knowledge/common/motion-prompt.md`。没有时序模块时，禁止把整段打斗压进一个提示词；应使用多个 3～5 秒镜头，每个镜头只包含一个主要动作。

快速动作必须走“关键帧序列 → 补帧 → 质量检查”流程。关键帧密度按动作速度动态选择，默认静态 1–2、普通动作 2–4、快速动作 4–8 张/秒；不得只重复静态图。根据 Box B 能力动态选择 OpenPose、Depth、RIFE/FILM，并在身份漂移、姿态跳变或补帧重影时按知识库规则重试。

交给混合视频生产技能前，运行 `python scripts/export_hybrid_plan.py <project.json> --output-dir <目录>`，生成 `project-bible.json` 和 `shot-plan.json`。导出失败时补齐镜头数据，不得让执行端猜测缺失的动作状态。
