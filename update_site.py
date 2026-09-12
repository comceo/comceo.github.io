#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
update_site.py —— 全站索引一键自动更新（在 GitHub 仓库根目录运行）

自动完成两件事：
  1. 重新生成 sitemap.xml（扫描全部 .html，URL 统一为无扩展名最终地址）
  2. 重新生成 articles.html（「全部文章」目录页，按子目录分组，标题取自每页的 <title>）

以后发新文章的完整流程（在 Codespaces 终端里）：
  python3 update_site.py && git add -A && git commit -m "更新索引" && git push

特性：
  - 文章标题自动从 <title> 标签读取（与页面显示一致），读不到才用文件名
  - 自动跳过：index.html、articles.html 自身、404.html、新文章模板
  - README.html 进 sitemap，但不进文章目录页
  - 新出现的子目录自动成组，无需改脚本
"""

import html as html_mod
import os
import re
import urllib.parse
import xml.etree.ElementTree as ET

SITE = "https://314blog.com"
EXCLUDE_FILES = {"404.html", "新文章模板.html"}
CAT_NAMES = {
    "hqbs": "环球巴士", "xjfyt": "星际放映厅", "fxp": "飞行派", "flp": "FamilyPro",
    "nfxp": "奈飞小铺", "token": "AI Token 聚合平台", "workbuddy": "WorkBuddy",
    "images": "其他", "": "综合",
}
CAT_ORDER = ["", "hqbs", "xjfyt", "fxp", "flp", "nfxp", "token", "workbuddy", "images"]
NS = "http://www.sitemaps.org/schemas/sitemap/0.9"


def page_url(rel_path: str) -> str:
    """文件相对路径 → 线上最终 URL（无 .html 后缀）。"""
    p = rel_path.replace(os.sep, "/")
    if p == "index.html":
        return SITE + "/"
    if p.endswith("/index.html"):
        return SITE + "/" + p[: -len("index.html")]
    if p.endswith(".html"):
        p = p[:-5]
    return SITE + "/" + p


def encode_url(url: str) -> str:
    parts = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit(
        (parts.scheme, parts.netloc, urllib.parse.quote(parts.path), "", "")
    )


def extract_title(path: str, rel_path: str) -> str:
    """从 <title> 读标题，失败则用文件名。"""
    try:
        with open(path, encoding="utf-8") as f:
            m = re.search(r"<title>(.*?)</title>", f.read(4096), re.S | re.I)
            if m and m.group(1).strip():
                return m.group(1).strip()
    except Exception:
        pass
    name = os.path.basename(rel_path)
    return name[:-5] if name.endswith(".html") else name


def scan_repo(repo: str):
    entries = []  # (rel_path, url, title)
    for dirpath, dirnames, filenames in os.walk(repo):
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d != "node_modules"]
        for fn in filenames:
            if not fn.endswith(".html") or fn in EXCLUDE_FILES:
                continue
            rel = os.path.relpath(os.path.join(dirpath, fn), repo)
            entries.append((rel, page_url(rel), extract_title(os.path.join(dirpath, fn), rel)))
    entries.sort(key=lambda e: e[1])
    return entries


def write_sitemap(entries, out_path: str) -> None:
    ET.register_namespace("", NS)
    urlset = ET.Element(f"{{{NS}}}urlset")
    for _, url, _ in entries:
        u = ET.SubElement(urlset, f"{{{NS}}}url")
        ET.SubElement(u, f"{{{NS}}}loc").text = encode_url(url)
    tree = ET.ElementTree(urlset)
    ET.indent(tree, space="  ")
    tree.write(out_path, encoding="UTF-8", xml_declaration=True)


def write_articles(entries, out_path: str) -> int:
    from collections import defaultdict
    cats = defaultdict(list)
    for rel, url, title in entries:
        if rel in ("index.html", "articles.html"):
            continue
        if os.path.basename(rel).lower() == "readme.html":
            continue
        parts = rel.replace(os.sep, "/").split("/")
        cat = parts[0] if len(parts) > 1 else ""
        cats[cat].append((encode_url(url), title))

    order = [c for c in CAT_ORDER if c in cats] + [c for c in cats if c not in CAT_ORDER]
    total = sum(len(v) for v in cats.values())
    sections = ""
    for cat in order:
        items = "".join(
            f'<li><a href="{html_mod.escape(link, quote=True)}">{html_mod.escape(title)}</a></li>'
            for link, title in sorted(cats[cat], key=lambda x: x[1])
        )
        name = CAT_NAMES.get(cat, cat if cat else "综合")
        sections += f'<h2>{html_mod.escape(name)}（{len(cats[cat])} 篇）</h2>\n<ul>{items}</ul>\n'

    page = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>全部文章 - 314Blog</title>
<meta name="description" content="314Blog 全部文章目录：ChatGPT Plus、Claude Pro、Gemini 等海外 AI 服务订阅与合租教程汇总。">
<link rel="canonical" href="{SITE}/articles">
<style>
body{{max-width:820px;margin:0 auto;padding:32px 20px;font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;line-height:1.8;color:#333;background:#fff}}
h1{{font-size:28px;border-bottom:2px solid #eee;padding-bottom:12px}}
h2{{font-size:20px;margin-top:32px;border-left:4px solid #0366d6;padding-left:10px}}
ul{{list-style:none;padding-left:0}}
li{{padding:6px 0;border-bottom:1px dashed #eee}}
a{{color:#0366d6;text-decoration:none}}
a:hover{{text-decoration:underline}}
.back{{display:inline-block;margin-bottom:20px;color:#0366d6;text-decoration:none}}
.count{{color:#999;font-size:14px;font-weight:normal}}
</style>
</head>
<body>
<a class="back" href="/">← 返回首页</a>
<h1>全部文章 <span class="count">共 {total} 篇</span></h1>
<p>汇总本站所有教程与评测文章，点击标题即可阅读。</p>
{sections}
</body>
</html>'''
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(page)
    return total


def main() -> None:
    repo = os.getcwd()
    if not os.path.exists(os.path.join(repo, "index.html")):
        print("错误：当前目录没有 index.html，请在仓库根目录运行。")
        raise SystemExit(1)

    entries = scan_repo(repo)
    write_sitemap(entries, os.path.join(repo, "sitemap.xml"))
    total = write_articles(entries, os.path.join(repo, "articles.html"))
    print(f"✅ sitemap.xml 已更新（{len(entries)} 个页面）")
    print(f"✅ articles.html 已更新（{total} 篇文章）")
    print("\n提交部署：git add -A && git commit -m \"更新索引\" && git push")


if __name__ == "__main__":
    main()
