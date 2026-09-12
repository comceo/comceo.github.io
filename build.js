const fs = require('fs');
const path = require('path');
const { marked } = require('marked');

const ROOT = __dirname;
const OUT = path.join(ROOT, '_site');

if (fs.existsSync(OUT)) fs.rmSync(OUT, { recursive: true, force: true });
fs.mkdirSync(OUT, { recursive: true });

const SITE = 'https://314blog.com';
const sitemapUrls = [];
const articles = []; // { url, title, cat, isReadme }

// 构建时不复制到线上目录的文件（仅仓库内使用）
const SKIP_FILES = new Set(['build.js', 'package.json', 'package-lock.json']);

// 目录页的分组名称
const CAT_NAMES = {
  '': '综合',
  hqbs: '环球巴士', xjfyt: '星际放映厅', fxp: '飞行派', flp: 'FamilyPro',
  nfxp: '奈飞小铺', token: 'AI Token 聚合平台', workbuddy: 'WorkBuddy', images: '其他',
};
const CAT_ORDER = ['', 'hqbs', 'xjfyt', 'fxp', 'flp', 'nfxp', 'token', 'workbuddy', 'images'];

function esc(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function walk(dir) {
  for (const item of fs.readdirSync(dir)) {
    if (['_site', 'node_modules', '.git', '.github'].includes(item)) continue;
    const full = path.join(dir, item);
    const stat = fs.statSync(full);

    if (stat.isDirectory()) {
      walk(full);
      continue;
    }

    const rel = path.relative(ROOT, full);

    if (item.endsWith('.md')) {
      const md = fs.readFileSync(full, 'utf8');
      const titleMatch = md.match(/^#\s+(.+)$/m);
      const title = titleMatch ? titleMatch[1].trim() : item.replace(/\.md$/, '');
      const body = marked.parse(md);

      const noExt = rel.replace(/\.md$/, '').replace(/\\/g, '/');
      const pageUrl = `${SITE}/${encodeURI(noExt)}`;

      const html = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>${esc(title)}</title>
<meta name="description" content="${esc(title)}">
<!-- 【迁移模式】将来要把权重统一到 314blog.com 时，取消下面这行的注释（会把 canonical 加到所有文章页）：
<link rel="canonical" href="${pageUrl}">
-->
<style>
body{max-width:820px;margin:0 auto;padding:32px 20px;font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;line-height:1.8;color:#333;background:#fff}
h1{font-size:28px;border-bottom:2px solid #eee;padding-bottom:12px}
h2{font-size:22px;margin-top:32px}h3{font-size:18px;margin-top:24px}
img{max-width:100%;height:auto}
pre{background:#f6f8fa;padding:14px;border-radius:6px;overflow:auto}
code{background:#f6f8fa;padding:2px 5px;border-radius:4px;font-size:.9em}
a{color:#0366d6}
blockquote{border-left:4px solid #dfe2e5;margin:0;padding-left:16px;color:#6a737d}
.nav{display:flex;gap:16px;margin-bottom:20px}
.nav a{color:#0366d6;text-decoration:none;font-size:14px}
</style>
</head>
<body>
<div class="nav">
  <a href="/">← 返回首页</a>
  <a href="/articles">📚 全部文章</a>
</div>
${body}
</body>
</html>`;

      const outPath = path.join(OUT, rel.replace(/\.md$/, '.html'));
      fs.mkdirSync(path.dirname(outPath), { recursive: true });
      fs.writeFileSync(outPath, html);
      console.log('md -> html:', rel);

      // sitemap 与目录页统一使用无 .html 的最终地址（Pages 会把 .html 308 跳转到无扩展名）
      sitemapUrls.push(pageUrl);
      const cat = noExt.includes('/') ? noExt.split('/')[0] : '';
      articles.push({ url: pageUrl, title, cat, isReadme: /(^|\/)README$/i.test(noExt) });
    } else {
      if (SKIP_FILES.has(item) || item.endsWith('.py')) continue; // 构建脚本不上线
      const outPath = path.join(OUT, rel);
      fs.mkdirSync(path.dirname(outPath), { recursive: true });
      fs.copyFileSync(full, outPath);
      console.log('copy:', rel);
    }
  }
}
walk(ROOT);

// ===== 生成 sitemap.xml（首页 + 所有文章，无 .html 后缀）=====
sitemapUrls.unshift(SITE + '/');
const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${sitemapUrls.map(u => `  <url>\n    <loc>${u}</loc>\n  </url>`).join('\n')}
</urlset>`;
fs.writeFileSync(path.join(OUT, 'sitemap.xml'), sitemap);
console.log(`Sitemap generated with ${sitemapUrls.length} URLs`);

// ===== 生成 articles.html 全部文章目录页 =====
const groups = {};
for (const a of articles) {
  if (a.isReadme) continue;
  (groups[a.cat] = groups[a.cat] || []).push(a);
}
const orderedCats = [
  ...CAT_ORDER.filter(c => groups[c]),
  ...Object.keys(groups).filter(c => !CAT_ORDER.includes(c)),
];
let total = 0;
const sections = orderedCats.map(cat => {
  const list = groups[cat].sort((x, y) => x.title.localeCompare(y.title, 'zh'));
  total += list.length;
  const items = list.map(a => `<li><a href="${a.url}">${esc(a.title)}</a></li>`).join('');
  const name = CAT_NAMES[cat] || cat || '综合';
  return `<h2>${esc(name)}（${list.length} 篇）</h2>\n<ul>${items}</ul>`;
}).join('\n');

const articlesHtml = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>全部文章 - 314Blog</title>
<meta name="description" content="314Blog 全部文章目录：ChatGPT Plus、Claude Pro、Gemini 等海外 AI 服务订阅与合租教程汇总。">
<link rel="canonical" href="${SITE}/articles">
<style>
body{max-width:820px;margin:0 auto;padding:32px 20px;font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;line-height:1.8;color:#333;background:#fff}
h1{font-size:28px;border-bottom:2px solid #eee;padding-bottom:12px}
h2{font-size:20px;margin-top:32px;border-left:4px solid #0366d6;padding-left:10px}
ul{list-style:none;padding-left:0}
li{padding:6px 0;border-bottom:1px dashed #eee}
a{color:#0366d6;text-decoration:none}
a:hover{text-decoration:underline}
.back{display:inline-block;margin-bottom:20px;color:#0366d6;text-decoration:none}
.count{color:#999;font-size:14px;font-weight:normal}
</style>
</head>
<body>
<a class="back" href="/">← 返回首页</a>
<h1>全部文章 <span class="count">共 ${total} 篇</span></h1>
<p>汇总本站所有教程与评测文章，点击标题即可阅读。</p>
${sections}
</body>
</html>`;
fs.writeFileSync(path.join(OUT, 'articles.html'), articlesHtml);
console.log(`articles.html generated with ${total} articles`);

console.log('Build done!');
