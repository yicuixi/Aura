"""
JobHunter CLI
"""

import argparse
import asyncio
import logging
import subprocess
import sys
import time

from .config import Config, EDGE_PATH, DATA_DIR
from .crawler import crawl_boss
from .scorer import JobScorer
from .form_filler import FormFiller
from .tracker import Tracker

BROWSER_PROFILE_DIR = DATA_DIR / "edge_profile"


def _launch_debug_edge(port: int = 9222):
    """启动独立 Edge 实例（独立 profile），带远程调试端口"""
    profile_dir = str(BROWSER_PROFILE_DIR.resolve())
    cmd = [
        EDGE_PATH,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile_dir}",
    ]
    print(f"正在启动 Edge (调试端口 {port}, 独立配置目录)...")
    print("请在打开的浏览器中登录需要投递的网站，登录完成后不要关闭浏览器。")
    print("（登录状态会保存，下次 login 不用重新登录）")
    print("然后在另一个终端运行: python -m job_hunter fill \"<申请页URL>\"")
    print("按 Ctrl+C 可退出等待（浏览器会继续运行）\n")
    proc = subprocess.Popen(cmd)
    time.sleep(2)
    if proc.poll() is not None:
        print(f"Edge 已启动（进程已分离），调试端口 {port} 应该可用。")
    else:
        try:
            proc.wait()
        except KeyboardInterrupt:
            print("\n浏览器继续运行中，可以开始填表了。")


def main():
    parser = argparse.ArgumentParser(description="JobHunter - 本地AI自动求职")
    parser.add_argument("command", choices=[
        "crawl", "score", "fill", "test-fill", "login", "diagnose",
        "export", "stats", "init-config",
    ])
    parser.add_argument("url", nargs="?", default=None)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    config = Config.load()

    if args.command == "login":
        port = int(config.cdp_url.split(":")[-1]) if config.cdp_url else 9222
        _launch_debug_edge(port)
        return

    tracker = Tracker()

    if args.command == "crawl":
        jobs = asyncio.run(crawl_boss(config))
        tracker.save_jobs(jobs)
        print(f"爬取完成: {len(jobs)} 个岗位")

    elif args.command == "score":
        jobs = tracker.get_jobs()
        unscored = [j for j in jobs if j.match_score == 0]
        if unscored:
            JobScorer(config).score_all(unscored)
            tracker.save_jobs(unscored)
        jobs = tracker.get_jobs(min_score=config.min_score)
        for j in jobs:
            print(f"  {j.match_score:.1f} | {j.company} | {j.title}")

    elif args.command == "diagnose":
        url = args.url or "https://httpbin.org/forms/post"
        fields = asyncio.run(FormFiller(config).diagnose(url))
        labeled = [f for f in fields if f.get("label") or f.get("name") or f.get("placeholder")]
        req_count = sum(1 for f in fields if f.get("required"))
        prefilled = sum(1 for f in labeled if f.get("value"))
        print(f"\n共 {len(fields)} 个字段 | {len(labeled)} 有标签 | {req_count} 必填 | {prefilled} 已有值\n")
        for f in fields:
            lbl = f.get("label") or f.get("name") or f.get("placeholder") or "(无标签)"
            parts = []
            if f.get("required"):
                parts.append("*必填")
            if f.get("value"):
                parts.append(f'已填: {f["value"][:20]}')
            if f.get("options"):
                parts.append(f'可选: [{", ".join(o["t"] for o in f["options"][:5])}]')
            extra = f" ({', '.join(parts)})" if parts else ""
            print(f'  [{f["idx"]:2d}] "{lbl}" ({f["type"]}){extra}')

    elif args.command in ("fill", "test-fill"):
        url = args.url or "https://httpbin.org/forms/post"
        result = asyncio.run(FormFiller(config).fill(url))
        print(result["message"])

    elif args.command == "export":
        print(f"导出: {tracker.export_csv()}")

    elif args.command == "stats":
        s = tracker.stats()
        print(f"岗位: {s['total']} | 高分: {s['high_score']} | 已投递: {s['applied']}")

    elif args.command == "init-config":
        config.save()
        print("配置已生成: job_hunter/config.yaml")


if __name__ == "__main__":
    main()
