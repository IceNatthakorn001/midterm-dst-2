"""Build the study-notes website from the 'sum by claude' folders.

Usage:  python build.py
Output: ./docs  (served by GitHub Pages)
"""
import html
import json
import re
import shutil
from pathlib import Path

from markdown_it import MarkdownIt
from mdit_py_plugins.anchors import anchors_plugin
from PIL import Image

ROOT = Path(__file__).resolve().parent
YEAR = ROOT.parent
OUT = ROOT / "docs"
IMG_MAX_W = 1400

SUBJECTS = [
    {
        "slug": "network",
        "dir": YEAR / "Network" / "sum by claude",
        "code": "ITDS231",
        "name": "Computer Networks",
        "th": "เครือข่ายคอมพิวเตอร์",
        "icon": "🌐",
        "accent": "#0f766e",
        "order": ["Ch1-Intro", "Ch2-Application-Layer", "Network-Topography", "Internet-Architecture",
                  "Lecture5.0-DLP-Foundation", "Lecture5.1-Error-Detection", "Lecture5.2-Flow-Control",
                  "Lecture6.1-MAC", "Lecture6.2-Ethernet", "Lecture7-VLAN"],
    },
    {
        "slug": "soft-en",
        "dir": YEAR / "Soft-EN" / "sum by claude",
        "code": "ITDS261",
        "name": "Introduction to Software Engineering",
        "th": "วิศวกรรมซอฟต์แวร์",
        "icon": "🧩",
        "accent": "#7c3aed",
        "order": None,
    },
    {
        "slug": "architecture",
        "dir": YEAR / "Arcitecture" / "sum by claude",
        "code": "ITDS211",
        "name": "Computer Architecture & Operating Systems",
        "th": "สถาปัตยกรรมคอมพิวเตอร์และระบบปฏิบัติการ",
        "icon": "🖥️",
        "accent": "#c2410c",
        "order": ["Chapter00", "Chapter01", "Chapter02", "Chapter03", "Chapter04", "Chapter05",
                  "Chapter06", "Chapter07", "Chapter08", "Lecture1", "Lecture2", "Lecture3"],
    },
    {
        "slug": "systemlab",
        "dir": YEAR / "Systemlab" / "sum by claude",
        "code": "ITDS212",
        "name": "Computer System Lab",
        "th": "ปฏิบัติการระบบคอมพิวเตอร์ (Linux)",
        "icon": "🐧",
        "accent": "#1d4ed8",
        "order": ["L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8", "L9"],
    },
]

md = MarkdownIt("gfm-like", {"html": True, "linkify": False, "typographer": False})
md.use(anchors_plugin, min_level=2, max_level=3, slug_func=lambda s: slugify(s))

_slug_seen: dict = {}


def slugify(text: str) -> str:
    s = re.sub(r"[^\w฀-๿\s-]", "", text).strip().lower()
    s = re.sub(r"[\s_]+", "-", s) or "sec"
    n = _slug_seen.get(s, 0)
    _slug_seen[s] = n + 1
    return s if n == 0 else f"{s}-{n}"


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def slug_path(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9.-]+", "-", name).strip("-").lower()


# ---------------------------------------------------------------- templates
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Thai:wght@400;500;600;700'
         '&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">')

THEME_BOOT = ("<script>try{var t=localStorage.getItem('theme');if(t)document.documentElement.dataset.theme=t;}"
              "catch(e){}</script>")


def page(title, body, depth, accent="#2563eb", extra_head=""):
    base = "../" * depth
    return f"""<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
{THEME_BOOT}
{FONTS}
<link rel="stylesheet" href="{base}assets/style.css">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>📚</text></svg>">
<style>:root{{--accent:{accent}}}</style>
{extra_head}
</head>
<body>
<div id="progress"></div>
<header class="topbar">
  <a class="brand" href="{base}index.html">📚 <span>Study Notes</span></a>
  <div class="topbar-right">
    <button class="icon-btn" id="themeBtn" title="สลับโหมดมืด/สว่าง" aria-label="toggle theme">◐</button>
  </div>
</header>
{body}
<footer class="foot">สรุปโดย Claude จากสไลด์ประกอบการเรียน · Mahidol ICT ปี 2</footer>
<script src="{base}assets/app.js"></script>
</body>
</html>"""


# ---------------------------------------------------------------- content
def find_lessons(subj):
    folders = [p for p in subj["dir"].iterdir() if p.is_dir()]
    if subj["order"]:
        rank = {n: i for i, n in enumerate(subj["order"])}
        folders.sort(key=lambda p: (rank.get(p.name, 999), p.name))
    else:
        folders.sort(key=lambda p: p.name)
    lessons = []
    for f in folders:
        mds = sorted(f.glob("สรุป-*.md"))
        if not mds:
            continue
        quizzes = sorted(f.glob("quiz-*.html"))
        short = f / "สรุปสั้นๆ.md"
        text = mds[0].read_text(encoding="utf-8")
        m = re.search(r"^#\s+(.+)$", text, re.M)
        title = m.group(1).strip() if m else mds[0].stem
        title = re.sub(r"^สรุป\s*[:：]\s*", "", title)
        lessons.append({"folder": f, "slug": slug_path(f.name), "label": f.name, "title": title,
                        "md": text, "quiz": quizzes[0] if quizzes else None,
                        "short": short.read_text(encoding="utf-8") if short.exists() else None})
    return lessons


def find_reviews(subj):
    """standalone exam-review pages: <sum by claude>/Review-*/<page>.html"""
    reviews = []
    for f in sorted(p for p in subj["dir"].iterdir() if p.is_dir() and p.name.startswith("Review-")):
        pages = sorted(f.glob("*.html"))
        if not pages:
            continue
        text = pages[0].read_text(encoding="utf-8")
        m = re.search(r"<h1[^>]*>(.*?)</h1>", text, re.S)
        title = re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else f.name
        heads = [re.sub(r"<[^>]+>", "", h).strip() for h in re.findall(r"<h2[^>]*>(.*?)</h2>", text, re.S)]
        reviews.append({"slug": slug_path(f.name), "label": f.name, "title": title, "html": text, "heads": heads})
    return reviews


REVIEW_BAR = """<div style="padding:8px 16px;background:#eef0f7;border-bottom:1px solid #dcdfe9;font-size:.92rem;display:flex;gap:12px;flex-wrap:wrap">
<a href="../index.html" style="color:#3f51b5;text-decoration:none;font-weight:600">← {subject}</a>
<span style="color:#999">|</span>
<a href="../../index.html" style="color:#555;text-decoration:none">หน้าแรก</a>
</div>"""


def copy_image(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
        return
    if src.suffix.lower() in (".jpg", ".jpeg"):
        im = Image.open(src)
        if im.width > IMG_MAX_W:
            im = im.resize((IMG_MAX_W, round(im.height * IMG_MAX_W / im.width)), Image.LANCZOS)
        im.convert("RGB").save(dst, "JPEG", quality=76, optimize=True, progressive=True)
    else:
        shutil.copy2(src, dst)


def render_lesson(lesson, key="md"):
    global _slug_seen
    _slug_seen = {}
    text = lesson[key]
    text = re.sub(r"^#\s+.+\n", "", text, count=1)  # title rendered in the header
    # consecutive "> text" lines are separate notes in the source; keep them as separate paragraphs
    text = re.sub(r"^(>[ \t]*\S.*)\n(?=>[ \t]*[^\s\-*|\d>])", r"\1\n>\n", text, flags=re.M)
    body = md.render(text)
    # images: lazy + zoomable
    body = body.replace("<img ", '<img loading="lazy" ')
    # callouts inside blockquotes
    body = re.sub(r"<blockquote>", '<blockquote class="callout">', body)
    body = re.sub(r"<p>(💡)", r'<p class="c-tip">\1', body)
    body = re.sub(r"<p>(⚠️)", r'<p class="c-warn">\1', body)
    # tables scroll horizontally on small screens
    body = body.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")
    # table of contents from h2
    toc = []
    for m in re.finditer(r'<h2 id="([^"]+)">(.*?)</h2>', body):
        label = re.sub(r"<[^>]+>", "", m.group(2))
        if label.strip() == "สารบัญ":
            continue
        toc.append((m.group(1), label))
    # drop the markdown's own plain-text "สารบัญ" (the sidebar replaces it)
    body = re.sub(r'<h2 id="[^"]*">สารบัญ</h2>\s*<ol>.*?</ol>\s*(<hr />\s*)?', "", body, count=1, flags=re.S)
    return body, toc


QUIZ_BAR = """<div style="position:sticky;top:0;z-index:50;margin:-24px -16px 20px;padding:10px 16px;background:rgba(245,246,250,.92);backdrop-filter:blur(8px);border-bottom:1px solid #e3e5ee;display:flex;gap:12px;align-items:center;flex-wrap:wrap;font-size:.92rem">
<a href="index.html" style="color:#3f51b5;text-decoration:none;font-weight:600">← กลับไปอ่านสรุป</a>
<span style="color:#999">|</span>
<a href="../index.html" style="color:#555;text-decoration:none">{subject}</a>
<span style="color:#999">|</span>
<a href="../../index.html" style="color:#555;text-decoration:none">หน้าแรก</a>
</div>"""


def build():
    if OUT.exists():
        for p in OUT.iterdir():  # keep compressed images cache in place
            if p.name not in SUBJECT_SLUGS and p.name != "img-cache":
                shutil.rmtree(p) if p.is_dir() else p.unlink()
    OUT.mkdir(exist_ok=True)
    shutil.copytree(ROOT / "assets", OUT / "assets", dirs_exist_ok=True)
    (OUT / ".nojekyll").write_text("")

    search_index = []
    subject_cards = []
    for subj in SUBJECTS:
        lessons = find_lessons(subj)
        sdir = OUT / subj["slug"]
        sdir.mkdir(parents=True, exist_ok=True)
        # remove stale html (keep images)
        for p in sdir.rglob("*.html"):
            p.unlink()

        for i, les in enumerate(lessons):
            ldir = sdir / les["slug"]
            ldir.mkdir(parents=True, exist_ok=True)
            for img in list(les["folder"].glob("img/*")) + list(les["folder"].glob("diagrams/*.png")):
                copy_image(img, ldir / img.parent.name / img.name)

            for variant in (["md", "short"] if les["short"] else ["md"]):
              is_short = variant == "short"
              body, toc = render_lesson(les, variant)
              if not is_short:
                  full_toc = toc
              prev_l = lessons[i - 1] if i > 0 else None
              next_l = lessons[i + 1] if i + 1 < len(lessons) else None
              toc_html = "".join(f'<li><a href="#{a}">{esc(t)}</a></li>' for a, t in toc)
              quiz_btn = ('<a class="btn btn-quiz" href="quiz.html">📝 ทำแบบทดสอบ</a>' if les["quiz"] else "")
              switch_btn = ('' if not les["short"] else
                            '<a class="btn" href="index.html">📖 อ่านฉบับเต็ม</a>' if is_short else
                            '<a class="btn" href="short.html">⚡ อ่านสรุปสั้น</a>')
              page_name = "short.html" if is_short else "index.html"
              nb = lambda l: "short.html" if is_short and l["short"] else "index.html"
              pager = '<nav class="pager">'
              pager += (f'<a class="pg prev" href="../{prev_l["slug"]}/{nb(prev_l)}"><small>← บทก่อนหน้า</small>'
                        f'<span>{esc(prev_l["title"])}</span></a>' if prev_l else "<span></span>")
              pager += (f'<a class="pg next" href="../{next_l["slug"]}/{nb(next_l)}"><small>บทถัดไป →</small>'
                        f'<span>{esc(next_l["title"])}</span></a>' if next_l else "<span></span>")
              pager += "</nav>"
              quiz_end = (f'<div class="quiz-cta"><div><strong>อ่านจบแล้ว? ลองทดสอบความเข้าใจ</strong>'
                          f'<p>แบบทดสอบ 4 ตัวเลือก เฉลยพร้อมเหตุผลทันที</p></div>{quiz_btn}</div>'
                          if les["quiz"] else "")
              content = f"""
  <div class="lesson-layout">
    <aside class="toc" id="toc">
      <button class="toc-toggle" id="tocToggle">☰ สารบัญ</button>
      <div class="toc-inner">
        <a class="toc-back" href="../index.html">← {esc(subj['code'])} ทุกบท</a>
        <ol>{toc_html}</ol>
      </div>
    </aside>
    <main class="lesson">
      <div class="crumbs"><a href="../../index.html">หน้าแรก</a> / <a href="../index.html">{esc(subj['icon'])} {esc(subj['code'])}</a> / {esc(les['label'])}</div>
      <h1 class="lesson-title">{"⚡ สรุปสั้น · " if is_short else ""}{esc(les['title'])}</h1>
      <div class="lesson-actions">{switch_btn}{quiz_btn}</div>
      <article class="prose">{body}</article>
      {quiz_end}
      {pager}
    </main>
  </div>"""
              (ldir / page_name).write_text(
                  page(f"{'สรุปสั้น · ' if is_short else ''}{les['title']} · {subj['code']}", content, 2, subj["accent"]), encoding="utf-8")

            if les["quiz"]:
                q = les["quiz"].read_text(encoding="utf-8")
                bar = QUIZ_BAR.format(subject=esc(f"{subj['icon']} {subj['code']}"))
                q = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + "\n" + bar, q, count=1)
                q = q.replace("<head>", '<head>\n<meta name="viewport" content="width=device-width, initial-scale=1">', 1)
                (ldir / "quiz.html").write_text(q, encoding="utf-8")

            search_index.append({"s": subj["code"], "t": les["title"], "u": f"{subj['slug']}/{les['slug']}/index.html",
                                 "h": [t for _, t in full_toc]})

        reviews = find_reviews(subj)
        for rv in reviews:
            rdir = sdir / rv["slug"]
            rdir.mkdir(parents=True, exist_ok=True)
            bar = REVIEW_BAR.format(subject=esc(f"{subj['icon']} {subj['code']}"))
            rh = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + "\n" + bar, rv["html"], count=1)
            (rdir / "index.html").write_text(rh, encoding="utf-8")
            search_index.append({"s": subj["code"], "t": rv["title"], "u": f"{subj['slug']}/{rv['slug']}/index.html",
                                 "h": rv["heads"]})

        # subject page
        review_rows = "".join(
            f'<li class="lesson-row"><span class="num">⭐</span>'
            f'<a class="lesson-link" href="{rv["slug"]}/index.html"><small>{esc(rv["label"])}</small>'
            f'<span>{esc(rv["title"])}</span></a>'
            f'<div class="row-actions"><a class="chip chip-quiz" href="{rv["slug"]}/index.html">🎯 รีวิว + โจทย์</a></div></li>'
            for rv in reviews)
        review_block = (f'<h2 style="margin:24px 0 8px">🎯 รีวิวก่อนสอบ</h2><ol class="lesson-list">{review_rows}</ol>'
                        f'<h2 style="margin:24px 0 8px">📖 สรุปรายบท</h2>' if reviews else "")
        rows = ""
        for n, les in enumerate(lessons, 1):
            qlink = (f'<a class="chip chip-quiz" href="{les["slug"]}/quiz.html">📝 Quiz</a>' if les["quiz"] else "")
            slink = (f'<a class="chip" href="{les["slug"]}/short.html">⚡ สรุปสั้น</a>' if les["short"] else "")
            rows += (f'<li class="lesson-row"><span class="num">{n:02d}</span>'
                     f'<a class="lesson-link" href="{les["slug"]}/index.html"><small>{esc(les["label"])}</small>'
                     f'<span>{esc(les["title"])}</span></a>'
                     f'<div class="row-actions"><a class="chip" href="{les["slug"]}/index.html">📖 อ่าน</a>{slink}{qlink}</div></li>')
        nq = sum(1 for l in lessons if l["quiz"])
        sbody = f"""
<main class="wrap">
  <div class="crumbs"><a href="../index.html">หน้าแรก</a> / {esc(subj['code'])}</div>
  <section class="subject-hero">
    <div class="big-icon">{subj['icon']}</div>
    <div>
      <div class="code">{esc(subj['code'])}</div>
      <h1>{esc(subj['name'])}</h1>
      <p>{esc(subj['th'])} · {len(lessons)} บทสรุป · {nq} แบบทดสอบ</p>
    </div>
  </section>
  {review_block}<ol class="lesson-list">{rows}</ol>
</main>"""
        (sdir / "index.html").write_text(page(f"{subj['code']} {subj['name']}", sbody, 1, subj["accent"]),
                                         encoding="utf-8")
        subject_cards.append(
            f'<a class="subject-card" href="{subj["slug"]}/index.html" style="--accent:{subj["accent"]}">'
            f'<div class="sc-icon">{subj["icon"]}</div><div class="code">{esc(subj["code"])}</div>'
            f'<h2>{esc(subj["name"])}</h2><p>{esc(subj["th"])}</p>'
            f'<div class="sc-meta"><span>📖 {len(lessons)} บท</span><span>📝 {nq} quiz</span></div></a>')

    home = f"""
<main class="wrap">
  <section class="home-hero">
    <h1>สรุปบทเรียน ปี 2</h1>
    <p>อ่านสรุปทีละบท พร้อมรูปสไลด์ประกอบ แล้วทดสอบความเข้าใจด้วย quiz ท้ายบท</p>
    <div class="search">
      <input id="q" type="search" placeholder="ค้นหาหัวข้อ เช่น cache, VLAN, use case…" autocomplete="off">
      <ul id="results"></ul>
    </div>
  </section>
  <section class="subject-grid">{''.join(subject_cards)}</section>
</main>
<script>window.SEARCH_INDEX = {json.dumps(search_index, ensure_ascii=False)};</script>"""
    (OUT / "index.html").write_text(page("Study Notes · สรุปบทเรียน", home, 0), encoding="utf-8")
    print("built", sum(1 for _ in OUT.rglob("*.html")), "html files")


SUBJECT_SLUGS = {s["slug"] for s in SUBJECTS}

if __name__ == "__main__":
    build()
