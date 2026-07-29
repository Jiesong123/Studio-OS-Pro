# Studio OS Video

Studio OS Video 是面向 Karmabox 智能体盒子的本地优先视频创作能力：由 Box A 负责理解需求、路由 Skill、规划项目和调度任务，由 Box B 负责通过 ComfyUI、本地模型或外部 API 生成图片、视频、音频并完成渲染。

当前版本：**1.2.0**

## 适用架构

```text
用户需求
   ↓
Box A：Video Skill + Knowledge + Runtime Planner
   ↓ QSFP / HTTP / 内部传输
Box B：ComfyUI、本地文生图/图生视频模型、补帧和渲染工具
   ↓
视频、音频、字幕和可追踪 artifact
```

Box A 不把某个模型或 ComfyUI 节点写死，而是先读取 Box B 的能力声明，再选择可用 workflow。

## 主要能力

- 中文视频创作入口和类型路由；
- 产品视频、短剧、漫剧三类专业 Skill；
- 短剧角色、分集和连续性管理；
- 按动作速度动态规划关键帧密度；
- 关键帧序列生成和 RIFE/FILM/ffmpeg 补帧接口；
- 根据身份漂移、动作跳变、僵硬和补帧重影进行有界重试；
- 音频、对白、字幕、音乐、转场和统一时间线规划；
- Box B 实时能力探测、模型选择和队列感知；
- 中文分类知识库，覆盖产品、短剧、漫剧、镜头、音频、字幕和质量排查。
- 面向 T2I→I2V、T2V 和视频延长的生产镜头字段；
- 将 Studio OS 项目导出为 `project-bible.json` 与 `shot-plan.json` 的转换工具。

## 目录

```text
config/       Box A 和 Box B 的默认配置
docs/         Media Box 契约和时序生成接入说明
knowledge/    分类知识库
schemas/      项目、镜头和剧集数据结构
skill/        视频路由及专业创作 Skill
src/          Studio OS Video Runtime
tests/        Runtime 和创作模式测试
```

## 时序视频流程

没有 AnimateDiff 或其他时序模型时，动作镜头采用：

```text
动作拆解 → 中间关键帧 → ComfyUI 生成 → RIFE/FILM 补帧 → 质量检查 → 30fps 输出
```

默认关键帧密度是：静态 1–2 张/秒、普通动作 2–4 张/秒、快速动作 4–8 张/秒。该数值是起始值，Runtime 会依据 Box B 能力和质量反馈动态调整。

Box B 需要在 `/v1/capabilities` 声明是否支持：

```json
{
  "keyframe_generation": true,
  "interpolation_engines": ["rife"],
  "controlnets": ["openpose", "depth", "lineart"]
}
```

推荐注册的 workflow ID：

```text
keyframe_sequence_v1
frame_interpolation_rife_v1
frame_interpolation_film_v1
```

真实的 ComfyUI workflow JSON、Checkpoint 和节点名称应放在 Box B，不应写死在 Skill 中。

## 本地检查

```bash
PYTHONPATH=src python3 -m compileall -q src tests
PYTHONPATH=src python3 -c "from studio_os_video import VideoPipeline; print('runtime ok')"
```

如果环境安装了 pytest，可以运行：

```bash
pytest -q
```

## 部署后重启建议

拉取新版本后，不需要让模型凭感觉判断是否重启。使用部署检查脚本分析 Git 改动：

```bash
cd "$STUDIO_OS_VIDEO_ROOT"
git pull origin main
PYTHONPATH=src python3 scripts/restart_advisor.py --base <上一版本提交号>
```

也可以输出 JSON，供 Box A 或本地模型读取：

```bash
PYTHONPATH=src python3 scripts/restart_advisor.py \
  --base <上一版本提交号> \
  --json
```

脚本根据 [config/restart-policy.json](config/restart-policy.json) 将变更归类：

| 输出 | 建议 |
|---|---|
| `box_a_runtime: restart` | Runtime、配置或依赖改变，重启 Box A |
| `box_b_worker: restart` | Media Worker 或能力契约改变，重启 Box B Worker |
| `box_a_context: reload` | 只改 Skill、知识库或文档，重新加载上下文即可 |
| `comfyui: inspect` | 工作流改变，先检查缓存，通常不必立即重启 |
| `comfyui: restart` | 模型资源或自定义节点改变，重新加载模型或重启 ComfyUI |

脚本只给出建议，不会自动杀进程或重启服务。重启后应检查服务日志、Box B `/v1/capabilities`，并运行一个短测试任务。`runtime ok` 只能证明 Python 可以导入，不能单独证明正在运行的服务已经换成新代码。

## 上传到 GitHub

在你的 Git 克隆目录中执行：

```bash
git add README.md pyproject.toml config src schemas skill knowledge docs tests
git commit -m "Release Studio OS Video v1.1"
git push origin main
```

## 版本说明

### 1.2.0

- 扩展镜头 Schema，增加剧情、绑定、动作、摄影机、连续性、生产模式和三帧验收字段；
- 增加混合视频生产交接契约与 `export_hybrid_plan.py` 转换程序；
- 保持旧镜头项目兼容，在生产导出阶段严格检查缺失字段；
- 更新漫剧、短剧和视频入口 Skill，禁止执行端猜测动作承接；
- 增加转换测试和完整示例。
- 修复质量重试参数的浮点精度不稳定问题。

### 1.1.0

- 增加关键帧生成和补帧的 Runtime 规划；
- 增加 Box B 能力探测字段；
- 增加动态参数和质量失败后的有界重试；
- 增加时序生成知识库和接入文档；
- 补充中文 Skill、README 和视频质量规则。
