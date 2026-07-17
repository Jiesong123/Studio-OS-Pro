"""Print safe restart recommendations from Git changes.

This tool never stops or restarts a process. It only produces a report for
Box A or an operator to review before applying service-specific commands.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "config" / "restart-policy.json"


def git_files(base: str | None, head: str) -> list[str]:
    command = ["git", "diff", "--name-only"]
    command += [base, head] if base else [head]
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=True)
    files = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    # Include untracked files when inspecting the working tree.
    if not base and head == "HEAD":
        result = subprocess.run(["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, text=True, capture_output=True, check=True)
        files.update(line.strip() for line in result.stdout.splitlines() if line.strip())
    return sorted(files)


def advise(files: list[str]) -> dict[str, Any]:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    services: dict[str, dict[str, Any]] = {}
    unmatched: list[str] = []
    for path in files:
        matched = False
        for rule in policy["rules"]:
            if any(path == pattern or path.startswith(pattern) for pattern in rule["patterns"]):
                item = services.setdefault(rule["service"], {"action": "reload", "reasons": [], "files": []})
                if rule["action"] == "restart":
                    item["action"] = "restart"
                elif item["action"] != "restart":
                    item["action"] = rule["action"]
                item["reasons"].append(rule["reason"])
                item["files"].append(path)
                matched = True
        if not matched:
            unmatched.append(path)
    if unmatched:
        services["manual_review"] = {"action": policy["default_action"], "reasons": ["未匹配的文件需要人工判断"], "files": unmatched}
    return {"repository": str(ROOT), "changed_files": files, "services": services, "safe_to_auto_restart": False}


def main() -> None:
    parser = argparse.ArgumentParser(description="根据 Git 改动给出服务重启建议")
    parser.add_argument("--base", help="比较起点，例如上一版本 commit；默认检查工作区相对 HEAD 的改动")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = advise(git_files(args.base, args.head))
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return
    print(f"仓库: {report['repository']}")
    print(f"变更文件: {len(report['changed_files'])}")
    for service, item in report["services"].items():
        print(f"- {service}: {item['action']}；{'; '.join(sorted(set(item['reasons'])))}")
        for path in item["files"]:
            print(f"    {path}")
    print("安全策略：脚本只给建议，不自动重启服务。")


if __name__ == "__main__":
    main()
