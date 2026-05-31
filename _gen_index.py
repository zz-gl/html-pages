#!/usr/bin/env python3
"""自愈式索引生成器 — 扫描本目录所有 .html，按 git 提交时间倒序生成 index.html。

每次有新文档发布后调用一次即可：新文档（提交时间最新）自动排在最前，
无需手动 prepend，也不会重复。无 git 信息时回落到文件 mtime。

用法：  python3 _gen_index.py        # 在 html-pages 仓库根目录运行
"""
import html
import os
import re
import subprocess
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SITE_BASE = "https://zz-gl.github.io/html-pages"


def git_date(fn):
    """文件最近一次提交时间（ISO）。未入库则用 mtime。"""
    try:
        out = subprocess.run(
            ["git", "-C", HERE, "log", "-1", "--format=%aI", "--", fn],
            capture_output=True, text=True, timeout=15,
        ).stdout.strip()
        if out:
            return datetime.datetime.fromisoformat(out)
    except Exception:
        pass
    return datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(HERE, fn)), tz=datetime.timezone.utc)


def get_title(fn):
    try:
        with open(os.path.join(HERE, fn), encoding="utf-8") as f:
            head = f.read(8000)
        m = re.search(r"<title>(.*?)</title>", head, re.S | re.I)
        if m:
            return re.sub(r"\s+", " ", m.group(1)).strip()
    except Exception:
        pass
    return fn[:-5]


def classify(fn):
    if fn.startswith("x-follows"):
        return ("每日动态", "daily")
    if fn.startswith("x-topic"):
        return ("主题调研", "topic")
    return ("专题", "feature")


def collect():
    items = []
    for fn in os.listdir(HERE):
        if not fn.endswith(".html") or fn == "index.html" or fn.startswith("_"):
            continue
        dt = git_date(fn)
        cat, cls = classify(fn)
        items.append({
            "fn": fn, "title": get_title(fn), "dt": dt,
            "cat": cat, "cls": cls, "date": dt.strftime("%Y-%m-%d"),
        })
    items.sort(key=lambda x: x["dt"], reverse=True)
    return items


def render(items):
    n = len(items)
    rows = []
    for it in items:
        rows.append(
            f'      <a class="doc" data-cls="{it["cls"]}" '
            f'data-search="{html.escape((it["title"] + " " + it["cat"] + " " + it["date"]).lower(), quote=True)}" '
            f'href="{SITE_BASE}/{it["fn"]}">\n'
            f'        <span class="tag tag-{it["cls"]}">{it["cat"]}</span>\n'
            f'        <span class="doc-title">{html.escape(it["title"])}</span>\n'
            f'        <span class="doc-date">{it["date"]}</span>\n'
            f'      </a>'
        )
    rows_html = "\n".join(rows)
    updated = datetime.datetime.now(datetime.timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M")
    n_daily = sum(1 for i in items if i["cls"] == "daily")
    n_topic = sum(1 for i in items if i["cls"] == "topic")
    n_feat = n - n_daily - n_topic
    return TEMPLATE.format(
        rows=rows_html, n=n, n_daily=n_daily, n_topic=n_topic, n_feat=n_feat, updated=updated,
    )


TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN" data-theme="auto">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>文档导航 · zz-gl</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{{
  --primary:#a03b00;--on-primary:#fff;--secondary-container:#7b40e0;--accent-cyan:#00D4FF;
  --bg:#fff8f6;--surface-lowest:#fff;--surface-low:#fbf2ef;--surface:#f5ece9;
  --fg-1:#1e1b19;--fg-2:#594138;--fg-muted:#8d7166;--border:rgba(0,0,0,.07);--border-strong:rgba(0,0,0,.12);
  --green:#10b981;--blue:#3b82f6;
  --font-h:'Space Grotesk',ui-sans-serif,system-ui,sans-serif;
  --font-b:'Plus Jakarta Sans',ui-sans-serif,system-ui,sans-serif;
  --gradient:linear-gradient(135deg,#a03b00 0%,#7b40e0 100%);
}}
html[data-theme="dark"]{{--bg:#060B18;--surface-lowest:#101D35;--surface-low:#101D35;--surface:#162544;--fg-1:#F8FAFC;--fg-2:#CBD5E1;--fg-muted:#94A3B8;--border:rgba(255,255,255,.09);--border-strong:rgba(255,255,255,.16);--primary:#FF6B35;}}
@media (prefers-color-scheme:dark){{html[data-theme="auto"]{{--bg:#060B18;--surface-lowest:#101D35;--surface-low:#101D35;--surface:#162544;--fg-1:#F8FAFC;--fg-2:#CBD5E1;--fg-muted:#94A3B8;--border:rgba(255,255,255,.09);--border-strong:rgba(255,255,255,.16);--primary:#FF6B35;}}}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:var(--font-b);background:var(--bg);color:var(--fg-1);line-height:1.55;-webkit-font-smoothing:antialiased}}
.wrap{{max-width:860px;margin:0 auto;padding:16px 16px 64px}}
header{{background:var(--gradient);color:#fff;border-radius:24px;padding:32px 26px;margin-top:12px;position:relative;overflow:hidden}}
header::after{{content:"";position:absolute;inset:0;background:radial-gradient(circle at 82% 18%,rgba(255,255,255,.16),transparent 55%)}}
.eyebrow{{font-size:.75rem;letter-spacing:.14em;text-transform:uppercase;opacity:.85;font-weight:600}}
header h1{{font-family:var(--font-h);font-size:clamp(1.5rem,4vw,2.1rem);font-weight:700;margin:8px 0 6px}}
header p{{opacity:.92;font-size:.95rem;font-weight:300;max-width:48ch}}
.stats{{display:flex;flex-wrap:wrap;gap:8px;margin-top:18px;position:relative;z-index:1}}
.stat{{background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.22);padding:6px 12px;border-radius:9999px;font-size:.82rem;font-weight:500}}
.stat b{{font-family:var(--font-h)}}
.theme-toggle{{position:absolute;top:16px;right:16px;z-index:2;display:flex;gap:3px;background:rgba(0,0,0,.18);border-radius:9999px;padding:4px}}
.theme-toggle button{{background:none;border:none;color:rgba(255,255,255,.7);font-size:.85rem;cursor:pointer;padding:5px 9px;border-radius:9999px;font-family:var(--font-b)}}
.theme-toggle button[aria-pressed="true"]{{background:#fff;color:var(--primary)}}
.controls{{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:24px 0 16px}}
.search{{position:relative;flex:1;min-width:200px}}
.search input{{width:100%;padding:11px 14px 11px 38px;border-radius:9999px;border:1px solid var(--border-strong);background:var(--surface-lowest);color:var(--fg-1);font-family:var(--font-b);font-size:.92rem}}
.search input:focus-visible{{outline:2px solid var(--primary);outline-offset:1px}}
.search svg{{position:absolute;left:13px;top:50%;transform:translateY(-50%);color:var(--fg-muted)}}
.filters{{display:flex;gap:4px;background:var(--surface);padding:4px;border-radius:9999px}}
.filters button{{border:none;background:none;padding:7px 13px;border-radius:9999px;cursor:pointer;font-family:var(--font-b);font-size:.84rem;font-weight:500;color:var(--fg-2)}}
.filters button[aria-pressed="true"]{{background:var(--surface-lowest);color:var(--primary);box-shadow:0 1px 2px rgba(0,0,0,.06)}}
.list{{display:flex;flex-direction:column;gap:8px}}
.doc{{display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:12px;padding:14px 16px;background:var(--surface-lowest);border:1px solid var(--border);border-radius:14px;text-decoration:none;color:inherit;transition:border-color .15s,transform .15s}}
.doc:hover{{border-color:var(--primary);transform:translateX(2px)}}
.doc:focus-visible{{outline:2px solid var(--primary);outline-offset:1px}}
.tag{{font-size:.72rem;font-weight:600;padding:3px 9px;border-radius:9999px;white-space:nowrap}}
.tag-daily{{background:rgba(16,185,129,.14);color:#0f9b6c}}
.tag-topic{{background:rgba(123,64,224,.14);color:#7b40e0}}
.tag-feature{{background:rgba(59,130,246,.14);color:#2f6fd6}}
html[data-theme="dark"] .tag-daily,html[data-theme="dark"] .tag-topic,html[data-theme="dark"] .tag-feature{{filter:brightness(1.4)}}
.doc-title{{font-weight:500;font-size:.96rem;min-width:0}}
.doc-date{{font-family:var(--font-h);font-size:.82rem;color:var(--fg-muted);white-space:nowrap}}
.empty{{text-align:center;color:var(--fg-muted);padding:40px}}
footer{{margin-top:32px;text-align:center;color:var(--fg-muted);font-size:.8rem}}
@media (max-width:560px){{
  .doc{{grid-template-columns:auto 1fr;grid-template-rows:auto auto;gap:4px 10px}}
  .doc-date{{grid-column:2;justify-self:start}}
}}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="theme-toggle" role="group" aria-label="主题">
      <button data-set="auto" aria-pressed="true">自动</button>
      <button data-set="light" aria-pressed="false">浅</button>
      <button data-set="dark" aria-pressed="false">深</button>
    </div>
    <div class="eyebrow">文档导航</div>
    <h1>X 调研 & 动态汇总</h1>
    <p>所有已发布文档，最新在最前。点开即读，支持搜索与按类型筛选。</p>
    <div class="stats">
      <span class="stat">共 <b>{n}</b> 篇</span>
      <span class="stat">每日动态 <b>{n_daily}</b></span>
      <span class="stat">主题调研 <b>{n_topic}</b></span>
      <span class="stat">专题 <b>{n_feat}</b></span>
    </div>
  </header>

  <div class="controls">
    <div class="search">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
      <input type="search" id="q" placeholder="搜标题 / 日期…" aria-label="搜索文档">
    </div>
    <div class="filters" role="group" aria-label="类型筛选">
      <button data-f="all" aria-pressed="true">全部</button>
      <button data-f="daily" aria-pressed="false">每日</button>
      <button data-f="topic" aria-pressed="false">主题</button>
      <button data-f="feature" aria-pressed="false">专题</button>
    </div>
  </div>

  <div class="list" id="list">
{rows}
  </div>
  <p class="empty" id="empty" style="display:none">没有匹配的文档</p>

  <footer>自动生成于 {updated} · 新文档发布后自动置顶</footer>
</div>

<script>
var root=document.documentElement;
document.querySelectorAll('[data-set]').forEach(function(b){{
  b.addEventListener('click',function(){{root.setAttribute('data-theme',b.dataset.set);
    document.querySelectorAll('[data-set]').forEach(function(x){{x.setAttribute('aria-pressed',x===b);}});}});
}});
var q=document.getElementById('q'),list=document.getElementById('list'),empty=document.getElementById('empty');
var docs=[].slice.call(list.querySelectorAll('.doc')),flt='all';
function apply(){{
  var s=q.value.trim().toLowerCase(),shown=0;
  docs.forEach(function(d){{
    var ok=(flt==='all'||d.dataset.cls===flt)&&(!s||d.dataset.search.indexOf(s)>=0);
    d.style.display=ok?'':'none'; if(ok)shown++;
  }});
  empty.style.display=shown?'none':'';
}}
q.addEventListener('input',apply);
document.querySelectorAll('[data-f]').forEach(function(b){{
  b.addEventListener('click',function(){{flt=b.dataset.f;
    document.querySelectorAll('[data-f]').forEach(function(x){{x.setAttribute('aria-pressed',x===b);}});apply();}});
}});
</script>
</body>
</html>
"""


def main():
    items = collect()
    out = render(items)
    with open(os.path.join(HERE, "index.html"), "w", encoding="utf-8") as f:
        f.write(out)
    print(f"index.html 已生成：{len(items)} 篇文档（最新：{items[0]['date']} {items[0]['title'][:30]}）" if items else "无文档")


if __name__ == "__main__":
    main()
