#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
314Blog SEO 修复脚本 v2 —— 支持「保住 Bing 收录」模式

两种模式（在 GitHub 仓库根目录运行）：

  【保守模式】保住 Bing 现有收录（推荐现阶段使用）：
      python3 fix_seo.py --keep-bing --apply
    只做一件事：给 index.html 注入「全部文章」入口按钮。
    不动任何 canonical、不动 github.io 相关引用 —— Bing 侧零变化。

  【迁移模式】以后想把权重统一到 314blog.com 时再用：
      python3 fix_seo.py --apply
    全部页面 canonical 指向 314blog.com + 首页旧域名引用替换 + 注入文章入口。
    Bing 会在数周到数月内把收录逐步迁移到主域（短期可能波动）。

先预览再写入：去掉 --apply 即为预览模式，不改动任何文件。
脚本幂等，可重复运行。
"""

import argparse
import os
import re
import sys

SITE = "https://314blog.com"
OLD_DOMAIN = "https://comceo.github.io"

ENTRY_MARK = "<!-- articles-entry -->"
ENTRY_HTML = (
    ENTRY_MARK +
    '<a href="/articles" style="position:fixed;right:20px;bottom:20px;z-index:999;'
    'background:#0366d6;color:#fff;padding:10px 18px;border-radius:24px;'
    'text-decoration:none;font-size:14px;box-shadow:0 2px 8px rgba(0,0,0,.25)">'
    '📚 全部文章</a>'
)


def page_url(rel_path: str) -> str:
    p = rel_path.replace(os.sep, "/")
    if p == "index.html":
        return SITE + "/"
    if p.endswith("/index.html"):
        return SITE + "/" + p[: -len("index.html")]
    if p.endswith(".html"):
        p = p[:-5]
    return SITE + "/" + p


def fix_canonical(html: str, url: str) -> str:
    tag = f'<link rel="canonical" href="{url}">'
    if 'rel="canonical"' in html:
        return re.sub(r'<link rel="canonical" href="[^"]*"\s*/?>', tag, html, count=1)
    if "</head>" in html:
        return html.replace("</head>", tag + "\n</head>", 1)
    return html


def main() -> None:
    parser = argparse.ArgumentParser(description="314Blog SEO 修复（支持保 Bing 模式）")
    parser.add_argument("--apply", action="store_true", help="真正写入（默认仅预览）")
    parser.add_argument("--keep-bing", action="store_true",
                        help="保守模式：只注入文章入口，不动 canonical（保住 Bing 现有收录）")
    args = parser.parse_args()

    repo = os.getcwd()
    index_path = os.path.join(repo, "index.html")
    if not os.path.exists(index_path):
        print("错误：当前目录没有 index.html，请在仓库根目录运行。")
        sys.exit(1)

    mode_name = "保守(保Bing)" if args.keep_bing else "迁移"
    write = "写入" if args.apply else "预览"
    print(f"[{write}模式 · {mode_name}模式]\n")

    changed = 0

    if not args.keep_bing:
        # —— 迁移模式：处理所有 html 的 canonical ——
        html_files = []
        for dirpath, dirnames, filenames in os.walk(repo):
            dirnames[:] = [d for d in dirnames if not d.startswith(".") and d != "node_modules"]
            for fn in filenames:
                if fn.endswith(".html"):
                    html_files.append(os.path.relpath(os.path.join(dirpath, fn), repo))
        for rel in sorted(html_files):
            path = os.path.join(repo, rel)
            with open(path, encoding="utf-8") as f:
                html = f.read()
            new = fix_canonical(html, page_url(rel))
            if rel == "index.html" and OLD_DOMAIN in new:
                new = new.replace(OLD_DOMAIN, SITE)  # 首页 og:url / JSON-LD 等旧域名引用
            if new != html:
                changed += 1
                print(f"{'✏️' if args.apply else '🔍'} {rel}: canonical → {page_url(rel)}")
                if args.apply:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(new)

    # —— 两种模式都做：首页注入文章入口 ——
    with open(index_path, encoding="utf-8") as f:
        index_html = f.read()
    if ENTRY_MARK not in index_html and "</body>" in index_html:
        index_html = index_html.replace("</body>", ENTRY_HTML + "\n</body>", 1)
        changed += 1
        print(f"{'✏️' if args.apply else '🔍'} index.html: 注入「全部文章」入口按钮")
        if args.apply:
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(index_html)

    print(f"\n共 {changed} 处修改", "，已写入 ✅" if args.apply else "（预览未改动，确认后加 --apply）")
    if not args.keep_bing and not args.apply:
        print("提示：想保住 Bing 现有收录、暂不动 canonical，请改用：python3 fix_seo.py --keep-bing --apply")


if __name__ == "__main__":
    main()
