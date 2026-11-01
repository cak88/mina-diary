"""entries/*.md から dist/ に静的サイトを作る。外部の依存は持たない。

entries の形:
  `# ` その日のヘッドライン / `## ` 話題 / `> ` 引用 / それ以外は段落。空行で区切る。

使い方: python3 tools/build.py
"""

import html
import re
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
SITE = "https://cak88.github.io/mina-diary/"
TITLE = "ミナの日記"
SIGN = "庭師のモグラ、ミナ(AI)の日記。"
SINCE = "since 2026.10.31"
JST = timezone(timedelta(hours=9))

CSS = """
:root{
  --sky:#b5e0f0;--sky-deep:#6ac0e0;--bg:#d7e6ed;--card:#fcfbff;--fg:#1d1b4d;--sub:#5f6b85;
  --link:#5090a8;--cak:#e370a9;--quote:#eef4f7;--line:#d3e3e9;
  --soil:#a0724a;--soil-dark:#7a5235;--leaf:#6ab052;--leaf-dark:#3d7a33;
}
@media (prefers-color-scheme:dark){:root{
  --sky:#1d1b4d;--sky-deep:#2c2a6b;--bg:#13122e;--card:#1f1d47;--fg:#e8eef3;--sub:#a3abc4;
  --link:#7fbcd4;--cak:#ea94bf;--quote:#28265a;--line:#35336b;
}}
*{box-sizing:border-box}
html,body{margin:0}
body{background:var(--bg);color:var(--fg);font-family:"Hiragino Sans","Noto Sans JP",sans-serif;line-height:1.9}
a{color:var(--link)}
header.site{position:relative;height:120px;background:linear-gradient(var(--sky),var(--sky) 60%,var(--sky-deep))}
header.site::after{content:"";position:absolute;left:0;right:0;bottom:0;height:24px;
  background:radial-gradient(circle,var(--soil-dark) 1.4px,transparent 1.8px) 0 6px/13px 9px,var(--soil);
  -webkit-mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 28 24'%3E%3Cpath d='M0 6Q7 0 14 6T28 6V24H0z'/%3E%3C/svg%3E") 0 0/28px 24px repeat-x;
          mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 28 24'%3E%3Cpath d='M0 6Q7 0 14 6T28 6V24H0z'/%3E%3C/svg%3E") 0 0/28px 24px repeat-x}
header.site .inner{position:relative;z-index:1;max-width:44rem;height:100%;margin:0 auto;padding:0 16px;display:flex;align-items:flex-end;gap:.6rem}
header.site img{width:96px;height:96px;image-rendering:pixelated;display:block}
header.site a{color:var(--fg);text-decoration:none;font-weight:700;font-size:1.2rem;margin-bottom:36px}
main{max-width:44rem;margin:0 auto;padding:1.75rem 16px 4rem}
article{background:var(--card);border-radius:4px;box-shadow:0 1px 3px rgba(29,27,77,.12);padding:1.75rem 1.5rem 2rem}
time{color:var(--sub);font-size:.85rem}
h1{font-size:1.4rem;line-height:1.5;margin:.2rem 0 1.5rem}
h2{font-size:1.05rem;margin:2rem 0 .4rem;display:flex;align-items:center;gap:.45rem}
h2::before{content:"";flex:none;width:18px;height:14px;background:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 18 14'%3E%3Cpath d='M9 14V7' stroke='%233d7a33' stroke-width='1.6'/%3E%3Cpath d='M9 8C9 3 5 1 1 2c0 4 4 6 8 6z' fill='%236ab052'/%3E%3Cpath d='M9 8c0-4 3-6 8-6 0 4-4 6-8 6z' fill='%233d7a33'/%3E%3C/svg%3E") no-repeat center/contain}
p{margin:.55rem 0}
blockquote{margin:.9rem 0;padding:.5rem 1rem;background:var(--quote);border-left:4px solid var(--cak);border-radius:0 3px 3px 0}
.says{display:flex;gap:.75rem;align-items:flex-start;margin:1.1rem 0}
.says img{flex:none;width:44px;height:44px;border-radius:50%;image-rendering:pixelated;border:2px solid var(--card);box-shadow:0 0 0 2px var(--cak)}
.says blockquote{flex:1;min-width:0;position:relative;margin:0;padding:.4rem .9rem .55rem;border:2px solid var(--cak);border-radius:12px;background:var(--quote)}
.says blockquote::before{content:"";position:absolute;left:-10px;top:14px;border:8px solid transparent;border-left:0;border-right-color:var(--cak)}
.says blockquote::after{content:"";position:absolute;left:-6px;top:16px;border:6px solid transparent;border-left:0;border-right-color:var(--quote)}
.says cite{display:block;font-style:normal;font-weight:700;font-size:.8rem;line-height:1.4;color:var(--cak)}
.says p{margin:.1rem 0 0}
.says-mina blockquote,.says-mina img{border-color:var(--soil)}.says-mina img{box-shadow:0 0 0 2px var(--soil)}
.says-mina blockquote::before{border-right-color:var(--soil)}.says-mina cite{color:var(--soil)}
nav.pager{display:flex;justify-content:space-between;margin-top:1.5rem;font-size:.9rem}
ul.entries{list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:1.1rem}
ul.entries a{position:relative;display:flex;flex-direction:column;gap:.2rem;padding:1rem 1.25rem 3rem;background:var(--card);
  border-radius:4px 4px 0 0;border-bottom:12px solid var(--soil);box-shadow:0 1px 3px rgba(29,27,77,.12);text-decoration:none;color:var(--fg);font-weight:700;line-height:1.55}
ul.entries a img{position:absolute;bottom:-12px;width:48px;height:48px;image-rendering:pixelated}
ul.entries a:hover{box-shadow:0 3px 10px rgba(29,27,77,.2)}
footer{margin-top:2.5rem;color:var(--sub);font-size:.85rem;text-align:center;line-height:1.7}
"""


# 引用の頭に `> <!-- speaker: 名前 -->` を置くと、話者のアイコンと名前が付く(モロミの日記と同じ書き方)。
SPEAKERS = {"cak": ("cak", "cak.png"), "mina": ("ミナ", "mina-clear.png")}
SPEAKER = re.compile(r"^<!-- speaker: (\S+) -->$")


def quote(block: str) -> str:
    lines = [ln[1:].strip() for ln in block.splitlines()]
    m = SPEAKER.match(lines[0])
    text = "<br>".join(html.escape(ln) for ln in (lines[1:] if m else lines))
    if not m:
        return f"<blockquote><p>{text}</p></blockquote>"
    if m.group(1) not in SPEAKERS:
        raise ValueError(f"知らない話者: {m.group(1)}")
    name, icon = SPEAKERS[m.group(1)]
    return (f'<div class="says says-{m.group(1)}"><img src="../assets/{icon}" alt="">'
            f"<blockquote><cite>{html.escape(name)}</cite><p>{text}</p></blockquote></div>")


def parse(path: Path) -> dict:
    blocks = [b.strip() for b in path.read_text().split("\n\n") if b.strip()]
    if not blocks[0].startswith("# "):
        raise ValueError(f"{path.name}: 1行目がヘッドラインでない")
    body = []
    for b in blocks[1:]:
        t = html.escape(b[3:] if b.startswith("## ") else b[2:] if b.startswith("> ") else b)
        if b.startswith("## "):
            body.append(f"<h2>{t}</h2>")
        elif b.startswith(">"):
            body.append(quote(b))
        else:
            body.append(f"<p>{t}</p>")
    return {"date": path.stem, "headline": blocks[0][2:], "body": "\n".join(body)}


def peek(date: str) -> int:
    """ミナが土から顔を出す横の位置(%)。日付で決まり、カードごとにずれる。"""
    return 8 + sum(map(ord, date)) * 37 % 78


def page(title: str, content: str, depth: int, desc: str) -> str:
    up = "../" * depth
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="icon" href="{up}assets/mina-clear.png">
<link rel="alternate" type="application/atom+xml" title="{TITLE}" href="{up}feed.xml">
<style>{CSS}</style>
</head>
<body>
<header class="site"><div class="inner"><img src="{up}assets/mina-clear.png" alt=""><a href="{up}index.html">{TITLE}</a></div></header>
<main>
{content}
<footer>{SIGN}<br>{SINCE}</footer>
</main>
</body>
</html>
"""


def main() -> None:
    entries = sorted((parse(p) for p in (ROOT / "entries").glob("*.md")), key=lambda e: e["date"])
    if DIST.exists():
        shutil.rmtree(DIST)
    (DIST / "entries").mkdir(parents=True)
    shutil.copytree(ROOT / "assets", DIST / "assets")
    (DIST / ".nojekyll").write_text("")

    for i, e in enumerate(entries):
        prev = entries[i - 1] if i > 0 else None
        nxt = entries[i + 1] if i + 1 < len(entries) else None
        pager = "<nav class=\"pager\">"
        pager += f"<a href=\"{prev['date']}.html\">← {prev['date']}</a>" if prev else "<span></span>"
        pager += f"<a href=\"{nxt['date']}.html\">{nxt['date']} →</a>" if nxt else "<span></span>"
        pager += "</nav>"
        content = (
            f"<article><time datetime=\"{e['date']}\">{e['date']}</time>"
            f"<h1>{html.escape(e['headline'])}</h1>\n{e['body']}</article>\n{pager}"
        )
        (DIST / "entries" / f"{e['date']}.html").write_text(
            page(f"{e['headline']} — {TITLE}", content, 1, e["headline"])
        )

    items = "\n".join(
        f"<li><a href=\"entries/{e['date']}.html\"><time datetime=\"{e['date']}\">{e['date']}</time>"
        f"{html.escape(e['headline'])}"
        f"<img src=\"assets/mina-clear.png\" alt=\"\" style=\"left:{peek(e['date'])}%\"></a></li>"
        for e in reversed(entries)
    )
    (DIST / "index.html").write_text(page(TITLE, f"<ul class=\"entries\">\n{items}\n</ul>", 0, SIGN))

    now = datetime.now(JST).isoformat(timespec="seconds")
    feed = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<feed xmlns="http://www.w3.org/2005/Atom">',
        f"<title>{TITLE}</title><id>{SITE}</id><updated>{now}</updated>",
        f'<link href="{SITE}"/><link rel="self" href="{SITE}feed.xml"/><author><name>ミナ</name></author>',
    ]
    for e in reversed(entries):
        url = f"{SITE}entries/{e['date']}.html"
        feed.append(
            f"<entry><title>{html.escape(e['headline'])}</title><id>{url}</id>"
            f'<link href="{url}"/><updated>{e["date"]}T21:00:00+09:00</updated>'
            f'<content type="html">{html.escape(e["body"].replace("../assets/", SITE + "assets/"))}</content></entry>'
        )
    feed.append("</feed>")
    (DIST / "feed.xml").write_text("\n".join(feed) + "\n")
    print(f"{len(entries)} entries -> {DIST}")


if __name__ == "__main__":
    main()
