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
    {
        "slug": "web",
        "dir": YEAR / "Web" / "sum by claude",
        "code": "ITDS241",
        "name": "Web Technologies and Applications",
        "th": "เทคโนโลยีเว็บและการประยุกต์ (HTML/CSS/JavaScript)",
        "icon": "💻",
        "accent": "#be185d",
        "order": None,
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
        quizzes2 = sorted(f.glob("quiz2-*.html"))
        quizzes3 = sorted(f.glob("quiz3-*.html"))
        short = f / "สรุปสั้นๆ.md"
        text = mds[0].read_text(encoding="utf-8")
        if len(mds) > 1:
            # several summaries in one folder (e.g. a revised slide deck): publish them on one page
            text = "\n\n---\n\n".join([text] + [p.read_text(encoding="utf-8") for p in mds[1:]])
            text = re.sub(r"\[([^\]]*)\]\(สรุป-[^)]*\.md\)", r"**\1** (อยู่ถัดลงไปในหน้านี้)", text)
        m = re.search(r"^#\s+(.+)$", text, re.M)
        title = m.group(1).strip() if m else mds[0].stem
        title = re.sub(r"^สรุป\s*[:：]\s*", "", title)
        # interactive animations that belong to this lesson: <folder>/animation-*.html
        anims = []
        for p in sorted(f.glob("animation-*.html")):
            ah = p.read_text(encoding="utf-8")
            am = re.search(r"<h1[^>]*>(.*?)</h1>", ah, re.S)
            atitle = re.sub(r"<[^>]+>", "", am.group(1)).strip() if am else p.stem
            anims.append({"name": p.name, "title": atitle, "short": atitle.split(":")[0].strip(), "html": ah,
                          "heads": [re.sub(r"<[^>]+>", "", x).strip() for x in re.findall(r"<h2[^>]*>(.*?)</h2>", ah, re.S)]})
        lessons.append({"folder": f, "slug": slug_path(f.name), "label": f.name, "title": title, "anims": anims,
                        "md": text, "quiz": quizzes[0] if quizzes else None,
                        "quiz2": quizzes2[0] if quizzes2 else None,
                        "quiz3": quizzes3[0] if quizzes3 else None,
                        "short": short.read_text(encoding="utf-8") if short.exists() else None})
    return lessons


def find_reviews(subj, prefix="Review-"):
    """standalone pages: <sum by claude>/Review-*/<page>.html (also Animation-*)"""
    reviews = []
    order = ["Stop-and-Wait", "GBN", "SR"]  # teaching order for Animation-* pages
    rank = lambda p: next((i for i, k in enumerate(order) if k in p.name), len(order))
    for f in sorted((p for p in subj["dir"].iterdir() if p.is_dir() and p.name.startswith(prefix)), key=lambda p: (rank(p), p.name)):
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


ANIM_BAR = """<div style="padding:8px 16px;background:#eef0f7;border-bottom:1px solid #dcdfe9;font-size:.92rem;display:flex;gap:12px;flex-wrap:wrap">
<a href="index.html" style="color:#3f51b5;text-decoration:none;font-weight:600">← กลับไปอ่านสรุป {lesson}</a>
<span style="color:#999">|</span>
<a href="../index.html" style="color:#555;text-decoration:none">{subject}</a>
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


QUIZPAGE_BAR = """<div style="position:sticky;top:0;z-index:50;margin:-24px -16px 20px;padding:10px 16px;background:rgba(245,246,250,.92);backdrop-filter:blur(8px);border-bottom:1px solid #e3e5ee;display:flex;gap:12px;align-items:center;flex-wrap:wrap;font-size:.92rem">
<a href="../index.html" style="color:#3f51b5;text-decoration:none;font-weight:600">← {subject}</a>
<span style="color:#999">|</span>
<a href="../../index.html" style="color:#555;text-decoration:none">หน้าแรก</a>
</div>"""

QUIZ_BAR = """<div style="position:sticky;top:0;z-index:50;margin:-24px -16px 20px;padding:10px 16px;background:rgba(245,246,250,.92);backdrop-filter:blur(8px);border-bottom:1px solid #e3e5ee;display:flex;gap:12px;align-items:center;flex-wrap:wrap;font-size:.92rem">
<a href="index.html" style="color:#3f51b5;text-decoration:none;font-weight:600">← กลับไปอ่านสรุป</a>
<span style="color:#999">|</span>
<a href="../index.html" style="color:#555;text-decoration:none">{subject}</a>
<span style="color:#999">|</span>
<a href="../../index.html" style="color:#555;text-decoration:none">หน้าแรก</a>
</div>"""


# ---------------------------------------------------------------- ITDS211 subject page (card layout)
ARCH_KEY = "itds211-progress"


def arch_track_script(slug, href, title):
    """remember which chapter was opened last (localStorage) for the 'อ่านต่อ' banner"""
    return ("<script>try{var k=%s,d=JSON.parse(localStorage.getItem(k)||'{}');d.v=d.v||{};d.v[%s]=1;"
            "d.last={h:%s,t:%s};localStorage.setItem(k,JSON.stringify(d));}catch(e){}</script>"
            % tuple(json.dumps(x, ensure_ascii=False) for x in (ARCH_KEY, slug, href, title))) + ARCH_TOC_JS


# collapsible sidebar on ITDS211 lesson pages (state kept in localStorage)
ARCH_TOC_JS = """<script>
(function(){var K='itds211-toc',r=document.documentElement;
try{if(localStorage.getItem(K)==='0')r.classList.add('toc-hidden');}catch(e){}
function set(h){r.classList.toggle('toc-hidden',h);try{localStorage.setItem(K,h?'0':'1');}catch(e){}}
document.addEventListener('click',function(e){var b=e.target.closest&&e.target.closest('[data-toc-collapse]');
if(b)set(!r.classList.contains('toc-hidden'));});
document.addEventListener('keydown',function(e){var t=e.target.tagName;
if(e.key==='['&&t!=='INPUT'&&t!=='TEXTAREA'&&!e.ctrlKey&&!e.metaKey)set(!r.classList.contains('toc-hidden'));});
})();</script>"""


def arch_topic(label):
    label = re.sub(r"\s*\(สไลด์[^)]*\)\s*$", "", html.unescape(label))
    return re.sub(r"^\d+\.\s*", "", label).strip()


ARCH_SKIP = ("คำศัพท์", "สรุปท้ายบท", "Course Outline", "Agenda", "Class Schedule", "Chapter Overview",
             "Course Logistics", "Summary")


def arch_subject_page(subj, lessons, nq, quizpages=()):
    groups = [("arch", "🖥️", "ส่วนที่ 1 · Computer Architecture", "Chapter 00–08 · ฮาร์ดแวร์ ตัวเลข หน่วยความจำ I/O pipeline"),
              ("os", "⚙️", "ส่วนที่ 2 · Operating Systems", "Lecture 1–3 · OS, Process, CPU Scheduling")]
    data, cards = [], {"arch": "", "os": ""}
    n_anim = sum(len(l["anims"]) for l in lessons)
    for les in lessons:
        g = "os" if les["label"].startswith("Lecture") else "arch"
        m = re.search(r"\d+", les["label"])
        num = (m.group(0).zfill(2) if g == "arch" else m.group(0)) if m else "•"
        title = re.sub(r"^(Chapter|Lecture)\s*\d+\s*[—–-]\s*", "", les["title"])
        topics = [(a, arch_topic(t)) for a, t in les["toc"]]
        shown = [t for _, t in topics if not any(s in t for s in ARCH_SKIP)][:5]
        s = les["slug"]
        btns = f'<a class="ax-btn ax-primary" href="{s}/index.html" data-l="{s}"><i>📖</i> อ่านเต็ม</a>'
        if les["short"]:
            btns += f'<a class="ax-btn" href="{s}/short.html" data-l="{s}"><i>⚡</i> สรุปสั้น</a>'
        for key, name, lbl in (("quiz", "quiz.html", "<i>📝</i> Quiz"), ("quiz2", "quiz2.html", "<i>📝</i> Quiz 2"),
                               ("quiz3", "quiz3.html", "<i>📝</i> Quiz 3")):
            if les[key]:
                btns += f'<a class="ax-btn ax-quiz" href="{s}/{name}" data-l="{s}">{lbl}</a>'
        anims = "".join(f'<a href="{s}/{a["name"]}" data-l="{s}" title="{esc(a["title"])}">▶ {esc(a["short"])}</a>'
                        for a in les["anims"])
        anim_row = f'<div class="ax-anims"><span>🎬 แอนิเมชัน</span>{anims}</div>' if anims else ""
        cards[g] += f"""
<li class="ax-card" data-g="{g}" data-s="{s}">
  <div class="ax-head">
    <span class="ax-num"><small>{"CH" if g == "arch" else "LEC"}</small>{num}</span>
    <a class="ax-title" href="{s}/index.html" data-l="{s}">{esc(title)}</a>
    <span class="ax-done" title="เคยเปิดบทนี้แล้ว">✓</span>
  </div>
  <p class="ax-topics">{esc(" · ".join(shown))}</p>
  <ul class="ax-hits"></ul>
  <div class="ax-actions">{btns}</div>
  {anim_row}
</li>"""
        data.append({"s": s, "f": " ".join([les["label"], les["title"]] + [t for _, t in topics]
                                         + [a["title"] for a in les["anims"]]).lower(),
                     "toc": [[a, t] for a, t in topics]})
    # real-exam quizzes: <sum by claude>/Quiz-*/ -> own group + filter tab
    quiz_cards = ""
    for qp in quizpages:
        s = qp["slug"]
        m = re.search(r"\d+", qp["label"])
        title = re.sub(r"^ข้อสอบจริง\s*", "", qp["title"])
        sm = re.search(r'<div class="sub">(.*?)</div>', qp["html"], re.S)
        info = re.sub(r"<[^>]+>", "", sm.group(1)).split(" — ")[0] if sm else ""
        quiz_cards += f"""
<li class="ax-card" data-g="quiz" data-s="{s}">
  <div class="ax-head">
    <span class="ax-num"><small>QUIZ</small>{m.group(0) if m else "•"}</span>
    <a class="ax-title" href="{s}/index.html" data-l="{s}">{esc(title)}</a>
    <span class="ax-done" title="เคยเปิดแล้ว">✓</span>
  </div>
  <p class="ax-topics">{esc(info)}</p>
  <ul class="ax-hits"></ul>
  <div class="ax-actions"><a class="ax-btn ax-quiz" href="{s}/index.html" data-l="{s}"><i>📝</i> ทำ Quiz</a></div>
</li>"""
        data.append({"s": s, "f": " ".join(["quiz", qp["label"], title, info]).lower(), "toc": []})
    cards["quiz"] = quiz_cards
    groups.append(("quiz", "📝", "Quiz · ข้อสอบจริง", "โจทย์จากการสอบ Quiz จริง แยกตามครั้ง"))
    n_os = sum(1 for l in lessons if l["label"].startswith("Lecture"))
    sections = "".join(
        f'<section class="ax-group" data-g="{g}"><div class="ax-ghead"><span class="ax-gicon">{ic}</span>'
        f'<div><h2>{h}</h2><p>{esc(sub)}</p></div></div><ol class="ax-grid">{cards[g]}</ol></section>'
        for g, ic, h, sub in groups if cards[g])
    return f"""
<main class="wrap ax-wrap">
  <div class="crumbs"><a href="../index.html">หน้าแรก</a> / {esc(subj['code'])}</div>
  <section class="subject-hero">
    <div class="big-icon">{subj['icon']}</div>
    <div>
      <div class="code">{esc(subj['code'])}</div>
      <h1>{esc(subj['name'])}</h1>
      <p>{esc(subj['th'])}</p>
      <div class="ax-stats"><span>📖 {len(lessons)} บท</span><span>📝 {nq} แบบทดสอบ</span><span>🎬 {n_anim} แอนิเมชัน</span></div>
    </div>
  </section>
  <a class="ax-continue" id="axContinue" hidden><span class="ax-play">▶</span><span><small>อ่านต่อจากครั้งก่อน</small><strong id="axContTitle"></strong></span></a>
  <div class="ax-tools">
    <div class="ax-search"><span>🔍</span><input id="axQ" type="search" placeholder="ค้นหาหัวข้อ เช่น cache, RAID, fork, IEEE 754…" autocomplete="off"><kbd>/</kbd></div>
    <div class="ax-tabs" role="tablist">
      <button class="on" data-f="all">ทั้งหมด <b>{len(lessons) + len(quizpages)}</b></button>
      <button data-f="arch">🖥️ Architecture <b>{len(lessons) - n_os}</b></button>
      <button data-f="os">⚙️ OS <b>{n_os}</b></button>
      {f'<button data-f="quiz">📝 Quiz <b>{len(quizpages)}</b></button>' if quizpages else ""}
    </div>
  </div>
  <div class="ax-legend"><span><i class="ax-dot p"></i>อ่านเต็ม = ฉบับละเอียด มีรูปสไลด์</span><span><i class="ax-dot"></i>สรุปสั้น = ทบทวนก่อนสอบ</span><span><i class="ax-dot q"></i>Quiz = ทดสอบ 4 ตัวเลือก</span></div>
  {sections}
  <p class="ax-empty" id="axEmpty" hidden>ไม่พบบทที่ตรงกับคำค้น — ลองคำอื่น เช่น "cache" หรือ "process"</p>
</main>
<script>window.ARCH = {json.dumps(data, ensure_ascii=False)};window.ARCH_KEY = {json.dumps(ARCH_KEY)};</script>
<script src="../assets/arch.js"></script>"""


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
              is_arch = subj["slug"] == "architecture"
              # toc labels are already HTML-escaped by the renderer; unescape first so "&" isn't shown as "&amp;"
              toc_html = "".join(f'<li><a href="#{a}">{esc(html.unescape(t)) if is_arch else esc(t)}</a></li>' for a, t in toc)
              collapse_btn = ('<button class="toc-collapse" data-toc-collapse title="ซ่อนสารบัญ (กด [)">«</button>'
                              '<button class="toc-rail" data-toc-collapse title="แสดงสารบัญ (กด [)"><span>☰</span>'
                              '<span class="toc-rail-label">สารบัญ</span></button>' if is_arch else "")
              quiz_btn = ('<a class="btn btn-quiz" href="quiz.html">📝 ทำแบบทดสอบ</a>' if les["quiz"] else "")
              if les["quiz2"]:
                  quiz_btn += '<a class="btn btn-quiz" href="quiz2.html">📝 แบบทดสอบชุดที่ 2</a>'
              if les["quiz3"]:
                  quiz_btn += '<a class="btn btn-quiz" href="quiz3.html">📝 แบบทดสอบชุดที่ 3</a>'
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
              anim_box = ('<div class="anim-box"><strong>🎬 แอนิเมชันของบทนี้</strong>'
                          + "".join(f'<a class="chip chip-quiz" href="{a["name"]}">▶ {esc(a["title"])}</a>' for a in les["anims"])
                          + '</div>' if les["anims"] else "")
              quiz_end = (f'<div class="quiz-cta"><div><strong>อ่านจบแล้ว? ลองทดสอบความเข้าใจ</strong>'
                          f'<p>แบบทดสอบ 4 ตัวเลือก เฉลยพร้อมเหตุผลทันที</p></div>{quiz_btn}</div>'
                          if les["quiz"] else "")
              content = f"""
  <div class="lesson-layout">
    <aside class="toc" id="toc">
      <button class="toc-toggle" id="tocToggle">☰ สารบัญ</button>{collapse_btn}
      <div class="toc-inner">
        <div class="toc-top"><a class="toc-back" href="../index.html">← {esc(subj['code'])} ทุกบท</a></div>
        <ol>{toc_html}</ol>
      </div>
    </aside>
    <main class="lesson">
      <div class="crumbs"><a href="../../index.html">หน้าแรก</a> / <a href="../index.html">{esc(subj['icon'])} {esc(subj['code'])}</a> / {esc(les['label'])}</div>
      <h1 class="lesson-title">{"⚡ สรุปสั้น · " if is_short else ""}{esc(les['title'])}</h1>
      <div class="lesson-actions">{switch_btn}{quiz_btn}</div>{anim_box}
      <article class="prose">{body}</article>
      {quiz_end}
      {pager}
    </main>
  </div>"""
              track = (arch_track_script(les["slug"], f'{les["slug"]}/{page_name}',
                                         ("⚡ สรุปสั้น · " if is_short else "📖 ") + les["title"])
                       if subj["slug"] == "architecture" else "")
              (ldir / page_name).write_text(
                  page(f"{'สรุปสั้น · ' if is_short else ''}{les['title']} · {subj['code']}", content, 2, subj["accent"], track), encoding="utf-8")
            les["toc"] = full_toc

            for key, out_name in (("quiz", "quiz.html"), ("quiz2", "quiz2.html"), ("quiz3", "quiz3.html")):
                if not les[key]:
                    continue
                q = les[key].read_text(encoding="utf-8")
                bar = QUIZ_BAR.format(subject=esc(f"{subj['icon']} {subj['code']}"))
                q = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + "\n" + bar, q, count=1)
                q = q.replace("<head>", '<head>\n<meta name="viewport" content="width=device-width, initial-scale=1">', 1)
                (ldir / out_name).write_text(q, encoding="utf-8")

            search_index.append({"s": subj["code"], "t": les["title"], "u": f"{subj['slug']}/{les['slug']}/index.html",
                                 "h": [t for _, t in full_toc]})

            for a in les["anims"]:
                bar = ANIM_BAR.format(lesson=esc(les["label"]), subject=esc(f"{subj['icon']} {subj['code']}"))
                ah = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + "\n" + bar, a["html"], count=1)
                (ldir / a["name"]).write_text(ah, encoding="utf-8")
                search_index.append({"s": subj["code"], "t": "🎬 " + a["title"],
                                     "u": f"{subj['slug']}/{les['slug']}/{a['name']}", "h": a["heads"]})

        reviews = find_reviews(subj)
        anims = find_reviews(subj, "Animation-")
        # standalone quizzes not tied to a summary: <sum by claude>/Quiz-*/quiz-*.html
        quizpages = find_reviews(subj, "Quiz-")
        for qp in quizpages:
            qdir = sdir / qp["slug"]
            qdir.mkdir(parents=True, exist_ok=True)
            bar = QUIZPAGE_BAR.format(subject=esc(f"{subj['icon']} {subj['code']}"))
            # first set (quiz-*) -> index.html, second set (quiz2-*) -> quiz2.html
            q2files = sorted((subj["dir"] / qp["label"]).glob("quiz2-*.html"))
            qp["quiz2"] = bool(q2files)
            for out_name, text in [("index.html", qp["html"])] + [("quiz2.html", f.read_text(encoding="utf-8")) for f in q2files[:1]]:
                q = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + "\n" + bar, text, count=1)
                q = q.replace("<head>", '<head>\n<meta name="viewport" content="width=device-width, initial-scale=1">', 1)
                (qdir / out_name).write_text(q, encoding="utf-8")
            qp["title"] = re.sub(r"^Quiz:\s*", "", qp["title"])
            search_index.append({"s": subj["code"], "t": qp["title"], "u": f"{subj['slug']}/{qp['slug']}/index.html", "h": []})
        for rv in reviews + anims:
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
        anim_rows = "".join(
            f'<li class="lesson-row"><span class="num">🎬</span>'
            f'<a class="lesson-link" href="{rv["slug"]}/index.html"><small>{esc(rv["label"])}</small>'
            f'<span>{esc(rv["title"])}</span></a>'
            f'<div class="row-actions"><a class="chip chip-quiz" href="{rv["slug"]}/index.html">▶ ดูแอนิเมชัน</a></div></li>'
            for rv in anims)
        quiz_rows = "".join(
            f'<li class="lesson-row"><span class="num">📝</span>'
            f'<a class="lesson-link" href="{qp["slug"]}/index.html"><small>{esc(qp["label"])}</small>'
            f'<span>{esc(qp["title"])}</span></a>'
            f'<div class="row-actions"><a class="chip chip-quiz" href="{qp["slug"]}/index.html">📝 Quiz</a>'
            + (f'<a class="chip chip-quiz" href="{qp["slug"]}/quiz2.html">🧩 Quiz 2 เติมโค้ด</a>' if qp["quiz2"] else "")
            + '</div></li>'
            for qp in quizpages)
        review_block = ((f'<h2 style="margin:24px 0 8px">📝 แบบทดสอบ</h2><ol class="lesson-list">{quiz_rows}</ol>' if quizpages else "")
                        + (f'<h2 style="margin:24px 0 8px">🎯 รีวิวก่อนสอบ</h2><ol class="lesson-list">{review_rows}</ol>' if reviews else "")
                        + (f'<h2 style="margin:24px 0 8px">🎬 Animation</h2><ol class="lesson-list">{anim_rows}</ol>' if anims else "")
                        + (f'<h2 style="margin:24px 0 8px">📖 สรุปรายบท</h2>' if (reviews or anims or quizpages) and lessons else ""))
        rows = ""
        for n, les in enumerate(lessons, 1):
            qlink = (f'<a class="chip chip-quiz" href="{les["slug"]}/quiz.html">📝 Quiz</a>' if les["quiz"] else "")
            if les["quiz2"]:
                qlink += f'<a class="chip chip-quiz" href="{les["slug"]}/quiz2.html">📝 Quiz 2</a>'
            if les["quiz3"]:
                qlink += f'<a class="chip chip-quiz" href="{les["slug"]}/quiz3.html">📝 Quiz 3</a>'
            slink = (f'<a class="chip" href="{les["slug"]}/short.html">⚡ สรุปสั้น</a>' if les["short"] else "")
            qlink += "".join(f'<a class="chip chip-quiz" href="{les["slug"]}/{a["name"]}">🎬 {esc(a["short"])}</a>'
                             for a in les["anims"])
            rows += (f'<li class="lesson-row"><span class="num">{n:02d}</span>'
                     f'<a class="lesson-link" href="{les["slug"]}/index.html"><small>{esc(les["label"])}</small>'
                     f'<span>{esc(les["title"])}</span></a>'
                     f'<div class="row-actions"><a class="chip" href="{les["slug"]}/index.html">📖 อ่าน</a>{slink}{qlink}</div></li>')
        nq = sum(bool(l["quiz"]) + bool(l["quiz2"]) + bool(l["quiz3"]) for l in lessons) + sum(1 + qp["quiz2"] for qp in quizpages)
        if subj["slug"] == "architecture":
            sbody = arch_subject_page(subj, lessons, nq, quizpages)
        else:
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
            f'<div class="sc-meta"><span>{f"📖 {len(lessons)} บท" if lessons else f"🎯 {len(reviews)} รีวิว"}</span><span>📝 {nq} quiz</span></div></a>')

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
