const fs = require('fs');
const path = require('path');
const { marked } = require('marked');

const ROOT = __dirname;
const OUT = path.join(ROOT, '_site');

if (fs.existsSync(OUT)) fs.rmSync(OUT, { recursive: true, force: true });
fs.mkdirSync(OUT, { recursive: true });

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

      const html = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>${title}</title>
<meta name="description" content="${title}">
<style>
body{max-width:820px;margin:0 auto;padding:32px 20px;font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;line-height:1.8;color:#333;background:#fff}
h1{font-size:28px;border-bottom:2px solid #eee;padding-bottom:12px}
h2{font-size:22px;margin-top:32px}h3{font-size:18px;margin-top:24px}
img{max-width:100%;height:auto}
pre{background:#f6f8fa;padding:14px;border-radius:6px;overflow:auto}
code{background:#f6f8fa;padding:2px 5px;border-radius:4px;font-size:.9em}
a{color:#0366d6}
blockquote{border-left:4px solid #dfe2e5;margin:0;padding-left:16px;color:#6a737d}
.back{display:inline-block;margin-bottom:20px;color:#0366d6;text-decoration:none}
</style>
</head>
<body>
<a class="back" href="/">← 返回首页</a>
${body}
</body>
</html>`;

      const outPath = path.join(OUT, rel.replace(/\.md$/, '.html'));
      fs.mkdirSync(path.dirname(outPath), { recursive: true });
      fs.writeFileSync(outPath, html);
      console.log('md -> html:', rel);
    } else {
      const outPath = path.join(OUT, rel);
      fs.mkdirSync(path.dirname(outPath), { recursive: true });
      fs.copyFileSync(full, outPath);
      console.log('copy:', rel);
    }
  }
}
walk(ROOT);
console.log('Build done!');
