#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百度「普通收录」API 推送脚本 —— 把 sitemap 里的文章批量推送给百度

用途：
  sitemap 提交额度为 0 时，普通收录的 API 推送是另一条独立通道（额度分开计算）。

使用步骤：
  1. 登录百度搜索资源平台 https://ziyuan.baidu.com
     → 搜索服务 → 资源提交 → 普通收录 → 「API提交」
     → 复制接口调用地址里的 token（形如 token=xxxxxxxx 的那一串）
  2. 运行：
       python3 baidu_push.py --token 你的token
     或先把 token 存进环境变量：
       export BD_TOKEN=你的token
       python3 baidu_push.py
  3. 先演练（不真正推送，只看会推哪些）：
       python3 baidu_push.py --token 你的token --dry-run

说明：
  - 脚本会自动把 sitemap 里 .html 结尾的 URL 转成无扩展名的最终 URL
    （Cloudflare Pages 会把 .html 308 跳转到无扩展名版本，推送最终地址更干净）
  - 已推送过的 URL 记录在脚本同目录的 pushed_urls.txt，重复运行不会重复推送
  - 默认跳过 README 目录说明页（低价值页面），想推送请加 --include-readme
  - 推送接口每天额度有限，返回的 remain 字段是当日剩余条数；额度用完明天再跑即可
"""

import argparse
import json
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET

SITEMAP_URL = "https://314blog.com/sitemap.xml"
SITE = "https://314blog.com"
PUSH_API = "http://data.zz.baidu.com/urls"
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pushed_urls.txt")
NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


def fetch_urls(sitemap_source: str, include_readme: bool) -> list[str]:
    """从 sitemap 读取全部 URL，去掉 .html 后缀，按需过滤 README 页。"""
    if sitemap_source.startswith("http"):
        with urllib.request.urlopen(sitemap_source, timeout=30) as resp:
            data = resp.read()
    else:
        with open(sitemap_source, "rb") as f:
            data = f.read()
    root = ET.fromstring(data)
    urls = []
    for u in root.findall(f"{NS}url"):
        loc = (u.find(f"{NS}loc").text or "").strip()
        if not loc or loc.rstrip("/") == SITE:
            continue  # 跳过首页
        if loc.endswith(".html"):
            loc = loc[:-5]  # .html → 无扩展名最终地址
        if not include_readme and loc.lower().endswith("/readme"):
            continue
        urls.append(loc)
    return urls


def load_pushed() -> set[str]:
    if not os.path.exists(STATE_FILE):
        return set()
    with open(STATE_FILE, encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


def save_pushed(urls: list[str]) -> None:
    with open(STATE_FILE, "a", encoding="utf-8") as f:
        for u in urls:
            f.write(u + "\n")


def push(token: str, urls: list[str]) -> dict:
    """调用百度普通收录推送接口。"""
    endpoint = f"{PUSH_API}?site={SITE}&token={token}"
    body = "\n".join(urls).encode("utf-8")
    req = urllib.request.Request(
        endpoint, data=body, headers={"Content-Type": "text/plain"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="百度普通收录 API 批量推送")
    parser.add_argument("--token", default=os.environ.get("BD_TOKEN", ""),
                        help="百度站长平台 API 提交的 token（或用环境变量 BD_TOKEN）")
    parser.add_argument("--sitemap", default=SITEMAP_URL,
                        help="sitemap 地址或本地文件路径")
    parser.add_argument("--include-readme", action="store_true",
                        help="连 README 目录说明页一起推送")
    parser.add_argument("--dry-run", action="store_true",
                        help="只列出将推送的 URL，不真正提交")
    args = parser.parse_args()

    urls = fetch_urls(args.sitemap, args.include_readme)
    pushed = load_pushed()
    pending = [u for u in urls if u not in pushed]

    print(f"sitemap 共 {len(urls)} 条，已推送过 {len(pushed)} 条，本次待推送 {len(pending)} 条")

    if not pending:
        print("没有需要推送的新 URL。")
        return

    if args.dry_run:
        print("\n--- 演练模式，将推送以下 URL ---")
        for u in pending:
            print(u)
        print("\n（去掉 --dry-run 后真正推送）")
        return

    if not args.token:
        print("错误：缺少 token。请用 --token 参数或 BD_TOKEN 环境变量提供。")
        sys.exit(1)

    try:
        result = push(args.token, pending)
    except urllib.error.HTTPError as e:
        print(f"推送失败 HTTP {e.code}：{e.read().decode('utf-8', 'ignore')}")
        print("常见原因：token 错误 / 站点未验证 / 当日额度为 0（明天再试）")
        sys.exit(1)

    if "success" in result:
        save_pushed(pending)
        print(f"推送成功 {result['success']} 条，今日剩余额度 {result.get('remain', '?')} 条")
    else:
        print(f"推送返回异常：{result}")
        print("若 error 为 quota 相关，说明 API 额度也是 0，请改用 robots.txt 里的 Sitemap 声明 + 抓取诊断过渡。")


if __name__ == "__main__":
    main()
