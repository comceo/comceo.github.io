#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bing IndexNow 即时推送脚本 —— 让 Bing 秒级知道你的文章

IndexNow 是 Bing 官方协议，推送后 Bing 会尽快抓取，比等蜘蛛上门快得多。

首次使用（两步）：
  1. 生成密钥文件：
       python3 bing_indexnow.py --gen-key
     会在当前目录生成一个 {密钥}.txt 文件 → 把它提交到仓库根目录
     （部署后能通过 https://314blog.com/{密钥}.txt 访问到）
  2. 等部署生效后推送：
       python3 bing_indexnow.py --key 你的密钥

日常使用：
  python3 bing_indexnow.py --key 你的密钥           # 只推新文章（自动记录已推过的）
  python3 bing_indexnow.py --key 你的密钥 --dry-run # 演练，看看会推哪些
  python3 bing_indexnow.py --key 你的密钥 --all     # 强制重推全部
"""

import argparse
import json
import os
import secrets
import sys
import urllib.request
import xml.etree.ElementTree as ET

SITEMAP_URL = "https://314blog.com/sitemap.xml"
HOST = "314blog.com"
API = "https://api.indexnow.org/indexnow"
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bing_pushed.txt")
NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


def gen_key() -> None:
    key = secrets.token_hex(16)  # 32 位十六进制
    filename = f"{key}.txt"
    with open(filename, "w") as f:
        f.write(key)
    print(f"密钥：{key}")
    print(f"已生成密钥文件：{filename}")
    print(f"\n下一步：把 {filename} 提交到仓库根目录，等部署生效后再运行推送：")
    print(f"  python3 bing_indexnow.py --key {key}")


def fetch_urls(sitemap_source: str) -> list[str]:
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
        if not loc:
            continue
        if loc.endswith(".html"):
            loc = loc[:-5]  # 统一为无扩展名最终地址
        if loc.lower().endswith("/readme"):
            continue
        urls.append(loc)
    return urls


def load_pushed() -> set[str]:
    if not os.path.exists(STATE_FILE):
        return set()
    with open(STATE_FILE, encoding="utf-8") as f:
        return {l.strip() for l in f if l.strip()}


def save_pushed(urls: list[str]) -> None:
    with open(STATE_FILE, "a", encoding="utf-8") as f:
        for u in urls:
            f.write(u + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Bing IndexNow 即时推送")
    parser.add_argument("--gen-key", action="store_true", help="生成密钥文件（首次使用）")
    parser.add_argument("--key", default=os.environ.get("INDEXNOW_KEY", ""), help="IndexNow 密钥")
    parser.add_argument("--sitemap", default=SITEMAP_URL, help="sitemap 地址或本地路径")
    parser.add_argument("--all", action="store_true", help="忽略记录，重推全部 URL")
    parser.add_argument("--dry-run", action="store_true", help="演练，不真正推送")
    args = parser.parse_args()

    if args.gen_key:
        gen_key()
        return

    urls = fetch_urls(args.sitemap)
    pending = urls if args.all else [u for u in urls if u not in load_pushed()]
    print(f"sitemap 共 {len(urls)} 条，本次待推送 {len(pending)} 条")

    if not pending:
        print("没有新 URL 需要推送。")
        return
    if args.dry_run:
        print("--- 演练模式 ---")
        for u in pending[:10]:
            print(u)
        if len(pending) > 10:
            print(f"... 等共 {len(pending)} 条")
        return
    if not args.key:
        print("错误：缺少密钥。先运行 --gen-key 生成，或用 --key 提供。")
        sys.exit(1)

    payload = json.dumps({
        "host": HOST,
        "key": args.key,
        "keyLocation": f"https://{HOST}/{args.key}.txt",
        "urlList": pending,
    }).encode("utf-8")
    req = urllib.request.Request(API, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            code = resp.getcode()
    except urllib.error.HTTPError as e:
        print(f"推送失败 HTTP {e.code}：{e.read().decode('utf-8', 'ignore')}")
        print("常见原因：密钥文件还没部署生效 / 密钥不匹配")
        sys.exit(1)

    if code == 200:
        save_pushed(pending)
        print(f"✅ 推送成功 {len(pending)} 条，Bing 会尽快抓取")
    else:
        print(f"返回 HTTP {code}，请检查密钥配置")


if __name__ == "__main__":
    main()
