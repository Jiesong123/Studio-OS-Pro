# 部署后的重启建议

更新完成后，Box A 不应凭感觉猜测是否重启。运行：

```bash
cd "$STUDIO_OS_VIDEO_ROOT"
PYTHONPATH=src python3 scripts/restart_advisor.py --base <上一版本提交号>
```

如果只想检查当前工作区：

```bash
PYTHONPATH=src python3 scripts/restart_advisor.py
```

脚本会按 `config/restart-policy.json` 将改动归类为：

- `box_a_runtime: restart`：Runtime、配置或依赖改变，重启 Box A；
- `box_b_worker: restart`：Media Worker 或能力契约改变，重启 Box B Worker；
- `box_a_context: reload`：Skill、知识库或文档改变，重新加载上下文即可；
- `comfyui: inspect`：工作流改变，先确认是否有缓存，通常不需要立即重启；
- `comfyui: restart`：模型资源或自定义节点改变，重新加载模型/重启 ComfyUI。

脚本只输出建议，不执行停止、杀进程或重启。Box A 可以读取 JSON 报告后调用已登记的服务管理器，但必须保留人工确认或受限的白名单命令。

验证重启是否生效：检查服务日志、Box B `/v1/capabilities`，并运行一个短测试任务。只看到 `runtime ok` 只能证明 Python 可以导入，不能证明旧进程已经换成新代码。
