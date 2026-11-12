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
        "accent": "#2b7a73",
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
        "accent": "#5f7a32",
        "order": ["L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8", "L9", "L10", "L11", "L12", "L13", "L14"],
    },
    {
        "slug": "architecture",
        "dir": YEAR / "Arcitecture" / "sum by claude",
        "code": "ITDS211",
        "name": "Computer Architecture & Operating Systems",
        "th": "สถาปัตยกรรมคอมพิวเตอร์และระบบปฏิบัติการ",
        "icon": "🖥️",
        "accent": "#b0552c",
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
        "accent": "#3b6787",
        "order": ["L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8", "L9"],
    },
    {
        "slug": "web",
        "dir": YEAR / "Web" / "sum by claude",
        "code": "ITDS241",
        "name": "Web Technologies and Applications",
        "th": "เทคโนโลยีเว็บและการประยุกต์ (HTML/CSS/JavaScript)",
        "icon": "💻",
        "accent": "#94496a",
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


def jsn(x) -> str:
    return json.dumps(x, ensure_ascii=False)


def slug_path(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9.-]+", "-", name).strip("-").lower()


def plain(label: str) -> str:
    """heading text without tags / html entities"""
    return html.unescape(re.sub(r"<[^>]+>", "", label)).strip()


def topic(label: str) -> str:
    """'3. ทำไม...? (สไลด์ 4–8)' -> 'ทำไม...?'"""
    label = re.sub(r"\s*\(สไลด์[^)]*\)\s*$", "", plain(label))
    return re.sub(r"^\d+(\.\d+)*\.?\s*", "", label).strip()


def short_title(title: str) -> str:
    """'Lecture 4 – Use Case Modeling' -> 'Use Case Modeling'"""
    t = re.sub(r"^(Chapter|Lecture|Ch\.?|Session)\s*[\d.]+\s*[—–:-]\s*", "", title, flags=re.I)
    return t or title


# ---------------------------------------------------------------- templates
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Thai+Looped:wght@400;500;600;700'
         '&family=Noto+Serif+Thai:wght@500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">')

THEME_BOOT = ("<script>try{var t=localStorage.getItem('theme');if(t)document.documentElement.dataset.theme=t;"
              "document.documentElement.dataset.bg=localStorage.getItem('bg')||'forest';"
              "if(localStorage.getItem('sn-nav')==='0')document.documentElement.classList.add('nav-hidden');}"
              "catch(e){}</script>")

ICON = ("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>"
        "<text y='.9em' font-size='90'>🌿</text></svg>")

LEAF = ('<svg class="leaf" viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">'
        '<path d="M4.5 19.5C4.5 11 10 4.8 20 4c-.8 10-7 15.5-15.5 15.5z" fill="currentColor"/>'
        '<path d="M4.8 19.2C8 15 11 12 15.5 8.5" stroke="var(--bg)" stroke-width="1.5" fill="none" stroke-linecap="round"/></svg>')


def page(title, body, depth, accent="#2f5d46", extra_head="", crumbs="", body_class="", scripts="", after=""):
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
<link rel="icon" href="{ICON}">
<style>:root{{--accent-base:{accent}}}</style>
{extra_head}
</head>
<body class="{body_class}">
<div id="progress" aria-hidden="true"></div>
<header class="topbar">
  <a class="brand" href="{base}index.html">{LEAF}<span>Study Notes</span></a>
  <nav class="topcrumbs">{crumbs}</nav>
  <button class="icon-btn bg-btn" id="bgBtn" title="เปลี่ยนพื้นหลัง (ป่าลึก / ภูเขา / ใบไม้)" aria-label="เปลี่ยนพื้นหลัง"><span class="bg-i bg-forest">🌲</span><span class="bg-i bg-hills">🌄</span><span class="bg-i bg-leaves">🍃</span></button>
  <button class="icon-btn" id="themeBtn" title="สลับโหมดมืด/สว่าง" aria-label="สลับโหมดมืด/สว่าง">
    <svg class="i-sun" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><circle cx="12" cy="12" r="4.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M4.9 19.1l1.8-1.8M17.3 6.7l1.8-1.8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
    <svg class="i-moon" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>
  </button>
</header>
{body}
<footer class="foot">สรุปโดย Claude จากสไลด์ประกอบการเรียน · Mahidol ICT ปี 2<span class="credit">ภาพพื้นหลังจาก Wikimedia Commons: <a href="https://commons.wikimedia.org/wiki/File:Mossy_branches_and_fern_leaves_(Unsplash).jpg">ป่า — Matthew Smith (CC0)</a> · <a href="https://commons.wikimedia.org/wiki/File:Breathtaking_beauty_of_Dzukou_Valley_in_Manipur-Nagaland_border_(edit).jpg">ภูเขา — Samudra Bikash Hazarika (CC BY-SA 4.0)</a> · <a href="https://commons.wikimedia.org/wiki/File:Fern_Leaves_(Unsplash).jpg">ใบเฟิร์น — Becky Phan (CC0)</a></span></footer>
<script>window.SN_BASE = {jsn(base)};</script>
{scripts}
<script src="{base}assets/app.js"></script>
{after}
</body>
</html>"""


# bar injected into standalone pages (quiz / review / animation) that bring their own CSS
def ext_bar(links, sticky=False):
    pos = "position:sticky;top:0;z-index:50;" if sticky else ""
    sep = '<span style="color:#cfc6b2">/</span>'
    items = sep.join(
        f'<a href="{h}" style="color:{"#26302a" if i == 0 else "#6d7468"};text-decoration:none;'
        f'font-weight:{600 if i == 0 else 400}">{t}</a>' for i, (h, t) in enumerate(links))
    return (f'<div style="{pos}display:flex;gap:10px;align-items:center;flex-wrap:wrap;padding:10px 18px;'
            'background:rgba(245,241,232,.95);backdrop-filter:blur(8px);border-bottom:1px solid #e3dccd;'
            'font:500 .92rem/1.5 \'IBM Plex Sans Thai Looped\',\'IBM Plex Sans Thai\',\'Segoe UI\',Tahoma,sans-serif">'
            f'<a href="{links[-1][0]}" style="text-decoration:none;font-weight:700;color:#2f5d46;margin-right:6px">🌿</a>{items}</div>')


def quiz_bar(links):
    items = '<span class="snq-sep">/</span>'.join(f'<a href="{h}">{t}</a>' for h, t in links)
    return f'<nav class="snq-bar"><a class="snq-home" href="{links[-1][0]}" aria-label="หน้าแรก">{LEAF}</a>{items}</nav>'


def inject_quiz(doc, bar, depth):
    base = "../" * depth
    head = (f'{THEME_BOOT}{FONTS}<link rel="stylesheet" href="{base}assets/quiz.css">'
            f'<link rel="icon" href="{ICON}">')
    doc = doc.replace("</head>", head + "\n</head>", 1)
    doc = doc.replace("<html", '<html class="snq"', 1)
    doc = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + "\n" + bar, doc, count=1)
    if 'name="viewport"' not in doc:
        doc = doc.replace("<head>", '<head>\n<meta name="viewport" content="width=device-width, initial-scale=1">', 1)
    return doc


def inject_bar(doc, bar, margin_fix=False):
    if margin_fix:  # quiz pages pad their <body>; pull the bar to the edges
        bar = bar.replace('<div style="', '<div style="margin:-24px calc(50% - 50vw) 20px;', 1)
    doc = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + "\n" + bar, doc, count=1)
    if 'name="viewport"' not in doc:
        doc = doc.replace("<head>", '<head>\n<meta name="viewport" content="width=device-width, initial-scale=1">', 1)
    return doc


# ---------------------------------------------------------------- content
def md_plain(s: str) -> str:
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", s)
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"[*_`#>|]", "", s).strip()


def read_minutes(md_text: str) -> int:
    """rough study-reading time: ~650 non-space characters per minute (Thai + tech terms)"""
    body = re.sub(r"```.*?```", lambda m: m.group(0)[: len(m.group(0)) // 2], md_text, flags=re.S)
    chars = len(re.sub(r"\s+", "", md_plain(body)))
    return max(1, round(chars / 650))


def lesson_desc(md_text: str, limit: int = 150) -> str:
    """one-line description for cards: the 'ภาพรวม' paragraph, else the first real paragraph"""
    m = re.search(r"^>\s*\*\*ภาพรวม[^*]*\*\*\s*[:：]?\s*(.+)$", md_text, re.M)
    if m:
        text = m.group(1)
    else:
        text = ""
        for line in md_text.splitlines()[1:]:
            ln = line.strip()
            if ln and not re.match(r"^(#|\||!|-|\*|\d+\.|>|```|---)", ln) and len(ln) > 30:
                text = ln
                break
    text = re.sub(r"\s+", " ", md_plain(text))
    text = re.sub(r"^ภาพรวม(บทนี้)?\s*[:：]?\s*", "", text)
    return text if len(text) <= limit else text[:limit].rstrip(" ,·(") + "…"


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
        quiz_list = [(k, n, l) for k, n, l, src in (
            ("quiz", "quiz.html", "ชุดที่ 1", quizzes), ("quiz2", "quiz2.html", "ชุดที่ 2", quizzes2),
            ("quiz3", "quiz3.html", "ชุดที่ 3", quizzes3)) if src]
        short_text = short.read_text(encoding="utf-8") if short.exists() else None
        lessons.append({"folder": f, "slug": slug_path(f.name), "label": f.name, "title": title, "anims": anims,
                        "desc": lesson_desc(text), "mins": read_minutes(text),
                        "short_mins": read_minutes(short_text) if short_text else 0,
                        "md": text, "quiz": quizzes[0] if quizzes else None,
                        "quiz2": quizzes2[0] if quizzes2 else None,
                        "quiz3": quizzes3[0] if quizzes3 else None, "quizzes": quiz_list,
                        "short": short_text})
    return lessons


def find_reviews(subj, prefix="Review-"):
    """standalone pages: <sum by claude>/Review-*/<page>.html (also Animation-*, Quiz-*)"""
    reviews = []
    order = ["Stop-and-Wait", "GBN", "SR"]  # teaching order for Animation-* pages
    rank = lambda p: next((i for i, k in enumerate(order) if k in p.name), len(order))
    for f in sorted((p for p in subj["dir"].iterdir() if p.is_dir() and p.name.startswith(prefix)), key=lambda p: (rank(p), p.name)):
        pages = sorted(f.glob("*.html"))
        if not pages:
            continue
        text = pages[0].read_text(encoding="utf-8")
        m = re.search(r"<h1[^>]*>(.*?)</h1>", text, re.S)
        title = plain(m.group(1)) if m else f.name
        heads = [plain(h) for h in re.findall(r"<h2[^>]*>(.*?)</h2>", text, re.S)]
        reviews.append({"slug": slug_path(f.name), "label": f.name, "title": title, "html": text, "heads": heads})
    return reviews


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
    body = body.replace("<img ", '<img loading="lazy" ')
    # callouts inside blockquotes
    body = re.sub(r"<blockquote>", '<blockquote class="callout">', body)
    body = re.sub(r"<p>(💡)", r'<p class="c-tip">\1', body)
    body = re.sub(r"<p>(⚠️)", r'<p class="c-warn">\1', body)
    # "**แก่น: ...**" core lines -> highlighted box (reread by skimming these)
    body = re.sub(r"<p><strong>แก่น\s*[:：]\s*", '<p class="core"><span class="core-tag">แก่น</span><strong>', body)
    # slide references in headings
    body = re.sub(r"<sub>\s*\((สไลด์[^)]*)\)\s*</sub>", r'<span class="slide-ref">\1</span>', body)
    # tables scroll horizontally on small screens
    body = body.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")
    # table of contents from h2
    toc = []
    for m in re.finditer(r'<h2 id="([^"]+)">(.*?)</h2>', body):
        label = plain(re.sub(r'<span class="slide-ref">.*?</span>', "", m.group(2)))
        if label == "สารบัญ":
            continue
        toc.append((m.group(1), label))
    # drop the markdown's own plain-text "สารบัญ" (the sidebar replaces it)
    body = re.sub(r'<h2 id="[^"]*">สารบัญ</h2>\s*<(ol|ul)[^>]*>.*?</\1>\s*(<hr />\s*)?', "", body, count=1, flags=re.S)
    return body, toc


SKIP_TOPICS = ("คำศัพท์", "สรุปท้ายบท", "คู่ที่มักสับสน", "Course Outline", "Agenda", "Class Schedule",
               "Chapter Overview", "Course Logistics", "Summary")


def quiz_menu(prefix, quizzes, data_l, cls="qm"):
    """one 'แบบทดสอบ' control instead of one button per quiz set"""
    if not quizzes:
        return ""
    if len(quizzes) == 1:
        k, name, label = quizzes[0]
        return f'<a class="btn btn-ghost" href="{prefix}{name}" data-l="{data_l}">📝 <span class="qm-l">แบบทดสอบ</span></a>'
    links = "".join(f'<a href="{prefix}{name}" data-l="{data_l}">📝 แบบทดสอบ{label}</a>' for k, name, label in quizzes)
    return (f'<details class="{cls}"><summary class="btn btn-ghost">📝 <span class="qm-l">แบบทดสอบ</span> <b>{len(quizzes)}</b>'
            f'<svg viewBox="0 0 20 20" width="14" height="14" aria-hidden="true"><path d="M5 8l5 5 5-5" fill="none" stroke="currentColor" stroke-width="2"/></svg>'
            f'</summary><div class="qm-pop">{links}</div></details>')


# ---------------------------------------------------------------- subject page (cards, all subjects)
def subject_page(subj, lessons, nq, reviews, anim_pages, quizpages):
    slug = subj["slug"]
    is_arch = slug == "architecture"
    if is_arch:
        groups = [("arch", "🖥️", "ส่วนที่ 1 · Computer Architecture", "Chapter 00–08 · ฮาร์ดแวร์ ตัวเลข หน่วยความจำ I/O pipeline"),
                  ("os", "⚙️", "ส่วนที่ 2 · Operating Systems", "Lecture 1–3 · OS, Process, CPU Scheduling")]
    else:
        groups = [("les", "📖", "สรุปรายบท", f"{len(lessons)} บท เรียงตามลำดับที่เรียน")]
    groups += [("review", "🎯", "รีวิวก่อนสอบ", "สรุปรวมหลายบท พร้อมโจทย์ฝึก"),
               ("quiz", "📝", "แบบทดสอบ", "ชุดข้อสอบที่ไม่ผูกกับบทใดบทหนึ่ง"),
               ("anim", "🎬", "แอนิเมชัน", "ดูการทำงานทีละขั้นแบบโต้ตอบได้")]
    data, cards = [], {g[0]: "" for g in groups}
    n_anim = sum(len(l["anims"]) for l in lessons) + len(anim_pages)

    def card(g, s, num_small, num, title, href, topics_txt, actions, extra="", meta=""):
        badge = (f'<span class="num"><small>{num_small}</small>{num}</span>' if num_small
                 else f'<span class="num num-icon">{num}</span>')
        meta_html = f'<div class="card-meta">{meta}</div>' if meta else ""
        return f"""
<li class="card" data-g="{g}" data-s="{s}">
  <div class="card-head">
    {badge}
    <div class="card-tt"><a class="card-title" href="{href}" data-l="{s}">{esc(title)}</a>{meta_html}</div>
    <span class="done" title="เคยเปิดแล้ว">✓</span>
  </div>
  <p class="card-topics">{esc(topics_txt)}</p>
  <ul class="hits"></ul>
  <div class="card-actions">{actions}</div>{extra}
</li>"""

    for i, les in enumerate(lessons, 1):
        g = ("os" if les["label"].startswith("Lecture") else "arch") if is_arch else "les"
        if is_arch:
            m = re.search(r"\d+", les["label"])
            num = (m.group(0).zfill(2) if g == "arch" else m.group(0)) if m else "•"
            small = "CH" if g == "arch" else "LEC"
        else:
            m = re.fullmatch(r"[A-Za-z]*\s*(\d+)", les["label"])  # L6 -> 06 (keeps gaps like a missing L5)
            num, small = (m.group(1).zfill(2) if m else f"{i:02d}"), "บท"
        topics = [(a, topic(t)) for a, t in les["toc"]]
        shown = [t for _, t in topics if t and not any(k in t for k in SKIP_TOPICS)][:4]
        s = les["slug"]
        actions = f'<a class="btn btn-primary" href="{s}/index.html" data-l="{s}">📖 อ่าน</a>'
        if les["short"]:
            actions += f'<a class="btn" href="{s}/short.html" data-l="{s}">⚡ สรุปสั้น</a>'
        actions += quiz_menu(f"{s}/", les["quizzes"], s)
        anims = "".join(f'<a href="{s}/{a["name"]}" data-l="{s}" title="{esc(a["title"])}">▶ {esc(a["short"])}</a>'
                        for a in les["anims"])
        extra = f'\n  <div class="card-anims"><span>🎬</span>{anims}</div>' if anims else ""
        meta = [f"⏱ ~{les['mins']} นาที", f"{len(topics)} หัวข้อ"]
        if les["short"]:
            meta.append(f"สรุปสั้น ~{les['short_mins']} นาที")
        cards[g] += card(g, s, small, num, short_title(les["title"]), f"{s}/index.html",
                         les["desc"] or " · ".join(shown), actions, extra,
                         "<span>" + "</span><span>".join(meta) + "</span>")
        data.append({"s": s, "f": " ".join([les["label"], les["title"]] + [t for _, t in topics]
                                         + [a["title"] for a in les["anims"]]).lower(),
                     "toc": [[a, t] for a, t in topics]})

    def simple_cards(g, items, icon, btn_label, topics_fn):
        for it in items:
            s = it["slug"]
            actions = f'<a class="btn btn-primary" href="{s}/index.html" data-l="{s}">{btn_label}</a>'
            if it.get("quiz2"):
                actions += f'<a class="btn" href="{s}/quiz2.html" data-l="{s}">🧩 ชุดที่ 2</a>'
            cards[g] += card(g, s, "", icon, it["title"], f"{s}/index.html", topics_fn(it), actions)
            data.append({"s": s, "f": " ".join([it["label"], it["title"]] + it["heads"]).lower(), "toc": []})

    def quiz_info(qp):
        sm = re.search(r'<div class="sub">(.*?)</div>', qp["html"], re.S)
        return re.sub(r"<[^>]+>", "", sm.group(1)).split(" — ")[0] if sm else qp["label"]

    simple_cards("review", reviews, "🎯", "เปิดรีวิว", lambda r: " · ".join(r["heads"][:4]))
    simple_cards("quiz", quizpages, "📝", "ทำแบบทดสอบ", quiz_info)
    simple_cards("anim", anim_pages, "🎬", "ดูแอนิเมชัน", lambda r: " · ".join(r["heads"][:4]))

    present = [g for g in groups if cards[g[0]]]
    counts = {g[0]: cards[g[0]].count('<li class="card"') for g in present}
    total = sum(counts.values())
    tabs = ""
    if len(present) > 1:
        tabs = '<div class="tabs" role="tablist"><button class="on" data-f="all">ทั้งหมด <b>%d</b></button>%s</div>' % (
            total, "".join(f'<button data-f="{g}">{ic} {esc(h.split("·")[-1].strip())} <b>{counts[g]}</b></button>'
                           for g, ic, h, _ in present))
    sections = "".join(
        f'<section class="group" data-g="{g}"><div class="group-head"><span class="group-icon">{ic}</span>'
        f'<div><h2>{h}</h2><p>{esc(sub)}</p></div></div><ol class="grid">{cards[g]}</ol></section>'
        for g, ic, h, sub in present)
    stats = [f"📖 {len(lessons)} บท"] if lessons else []
    stats += [f"📝 {nq} แบบทดสอบ"] if nq else []
    stats += [f"🎬 {n_anim} แอนิเมชัน"] if n_anim else []
    stats += [f"🎯 {len(reviews)} รีวิว"] if reviews else []
    body = f"""
<main class="wrap">
  <section class="subject-hero">
    <div class="big-icon">{subj['icon']}</div>
    <div>
      <div class="code">{esc(subj['code'])}</div>
      <h1>{esc(subj['name'])}</h1>
      <p>{esc(subj['th'])}</p>
      <div class="stats">{"".join(f"<span>{x}</span>" for x in stats)}</div>
    </div>
  </section>
  <a class="continue" id="cont" hidden><span class="continue-play">▶</span><span><small>อ่านต่อจากครั้งก่อน</small><strong id="contTitle"></strong></span></a>
  <div class="tools">
    <label class="searchbox"><svg viewBox="0 0 20 20" width="16" height="16" aria-hidden="true"><circle cx="9" cy="9" r="6" fill="none" stroke="currentColor" stroke-width="2"/><path d="M14 14l4 4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg><input id="sq" type="search" placeholder="ค้นหาหัวข้อในวิชานี้…" autocomplete="off"><kbd>/</kbd></label>
    {tabs}
  </div>
  {sections}
  <p class="empty" id="sEmpty" hidden>ไม่พบบทที่ตรงกับคำค้น ลองคำอื่นดูนะ</p>
</main>"""
    scripts = f"<script>window.SN_SUBJ = {jsn(slug)};window.SN_DATA = {jsn(data)};</script>"
    return body, scripts


# ---------------------------------------------------------------- lesson page
def lesson_page(subj, lessons, i, les, is_short, body, toc):
    s = les["slug"]
    page_name = "short.html" if is_short else "index.html"
    prev_l = lessons[i - 1] if i > 0 else None
    next_l = lessons[i + 1] if i + 1 < len(lessons) else None
    nb = lambda l: "short.html" if is_short and l["short"] else "index.html"
    # left: every lesson of this subject
    nav = "".join(
        f'<li{" class='cur'" if l is les else ""}><a href="../{l["slug"]}/{nb(l)}">'
        f'<span class="nl">{esc(l["label"])}</span>{esc(short_title(l["title"]))}</a></li>' for l in lessons)
    # right: sections of this page
    otp = "".join(f'<li><a href="#{a}">{esc(topic(t) or plain(t))}</a></li>' for a, t in toc)
    # version switch (full / short)
    if les["short"]:
        switch = (f'<div class="seg" role="group" aria-label="เลือกฉบับ">'
                  f'<a href="index.html"{" aria-current='page'" if not is_short else ""}>📖 ฉบับเต็ม</a>'
                  f'<a href="short.html"{" aria-current='page'" if is_short else ""}>⚡ สรุปสั้น</a></div>')
    else:
        switch = ""
    qmenu = quiz_menu("", les["quizzes"], s)
    anims = "".join(f'<a class="chip" href="{a["name"]}">🎬 {esc(a["short"])}</a>' for a in les["anims"])
    meta = f'<div class="lesson-meta">{switch}{qmenu}{anims}</div>' if (switch or qmenu or anims) else ""
    pager = '<nav class="pager">'
    pager += (f'<a class="pg prev" href="../{prev_l["slug"]}/{nb(prev_l)}"><small>← บทก่อนหน้า</small>'
              f'<span>{esc(prev_l["title"])}</span></a>' if prev_l else "<span></span>")
    pager += (f'<a class="pg next" href="../{next_l["slug"]}/{nb(next_l)}"><small>บทถัดไป →</small>'
              f'<span>{esc(next_l["title"])}</span></a>' if next_l else "<span></span>")
    pager += "</nav>"
    quiz_links = "".join(f'<a class="btn btn-primary" href="{n}">📝 แบบทดสอบ{lbl if len(les["quizzes"]) > 1 else ""}</a>'
                         for k, n, lbl in les["quizzes"])
    quiz_end = (f'<div class="end-cta"><div><strong>อ่านจบแล้ว ลองทดสอบความเข้าใจ</strong>'
                f'<p>ข้อสอบ 4 ตัวเลือก เฉลยพร้อมเหตุผลทันที ยิ่งลองตอบเองก่อนยิ่งจำได้ดี</p></div>'
                f'<div class="end-btns">{quiz_links}</div></div>' if les["quizzes"] else "")
    other = ("index.html" if is_short else "short.html") if les["short"] else ""
    bottom = (f'<nav class="bottombar">'
              f'<button type="button" id="sheetBtn">☰ <span>สารบัญ</span></button>'
              + (f'<a href="{other}">{"📖 <span>ฉบับเต็ม</span>" if is_short else "⚡ <span>สรุปสั้น</span>"}</a>' if other else "")
              + (f'<a href="{les["quizzes"][0][1]}">📝 <span>แบบทดสอบ</span></a>' if les["quizzes"] else "")
              + '<button type="button" id="topBtn">↑ <span>บนสุด</span></button></nav>')
    title = ("⚡ สรุปสั้น · " if is_short else "") + les["title"]
    content = f"""
<div class="lesson-layout">
  <aside class="lnav" aria-label="บทเรียนทั้งหมด">
    <div class="lnav-head"><a href="../index.html">{subj['icon']} {esc(subj['code'])}</a>
      <button class="lnav-hide" data-nav-toggle title="ซ่อนรายชื่อบท (กด [)" aria-label="ซ่อนรายชื่อบท">«</button></div>
    <ol>{nav}</ol>
  </aside>
  <button class="lnav-rail" data-nav-toggle title="แสดงรายชื่อบท (กด [)" aria-label="แสดงรายชื่อบท"><span>☰</span><span class="rail-label">บททั้งหมด</span></button>
  <main class="lesson" id="main">
    <div class="eyebrow"><a href="../index.html">{esc(subj['code'])}</a> · {esc(les['label'])}{" · สรุปสั้น" if is_short else ""}</div>
    <h1 class="lesson-title">{esc(les['title'])}</h1>
    <p class="read-meta">⏱ อ่านประมาณ {les["short_mins"] if is_short else les["mins"]} นาที · {len(toc)} หัวข้อ</p>
    {meta}
    <article class="prose">{body}</article>
    {quiz_end}
    {pager}
  </main>
  <aside class="otp" id="toc" aria-label="ในหน้านี้">
    <div class="otp-inner">
      <div class="otp-head"><span>ในหน้านี้</span><button type="button" class="otp-close" id="sheetClose" aria-label="ปิด">✕</button></div>
      <ol>{otp}</ol>
      {'<p class="otp-note">⭐ = เรื่องสำคัญ มักออกสอบ</p>' if "⭐" in body else ""}
    </div>
  </aside>
</div>
<div class="sheet-backdrop" id="sheetBackdrop"></div>
{bottom}"""
    crumbs = (f'<a href="../../index.html">หน้าแรก</a><span>/</span><a href="../index.html">{esc(subj["code"])}</a>'
              f'<span>/</span><b>{esc(les["label"])}</b>')
    track = {"k": f'{subj["slug"]}/{s}', "u": f'{subj["slug"]}/{s}/{page_name}', "t": title, "s": subj["code"]}
    return page(f"{'สรุปสั้น · ' if is_short else ''}{les['title']} · {subj['code']}", content, 2, subj["accent"],
                crumbs=crumbs, body_class="is-lesson", scripts=f"<script>window.SN_TRACK = {jsn(track)};</script>")


# ---------------------------------------------------------------- build
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
    home_lessons = {}
    for subj in SUBJECTS:
        lessons = find_lessons(subj)
        sdir = OUT / subj["slug"]
        sdir.mkdir(parents=True, exist_ok=True)
        for p in sdir.rglob("*.html"):  # remove stale html (keep images)
            p.unlink()
        code = f"{subj['icon']} {subj['code']}"

        # render all variants first (toc of every lesson is needed for the subject cards)
        rendered = []
        for les in lessons:
            out = {}
            for variant in (["md", "short"] if les["short"] else ["md"]):
                out[variant] = render_lesson(les, variant)
            les["toc"] = out["md"][1]
            rendered.append(out)

        for i, les in enumerate(lessons):
            ldir = sdir / les["slug"]
            ldir.mkdir(parents=True, exist_ok=True)
            for img in list(les["folder"].glob("img/*")) + list(les["folder"].glob("diagrams/*.png")):
                copy_image(img, ldir / img.parent.name / img.name)
            for variant, (body, toc) in rendered[i].items():
                is_short = variant == "short"
                (ldir / ("short.html" if is_short else "index.html")).write_text(
                    lesson_page(subj, lessons, i, les, is_short, body, toc), encoding="utf-8")

            for key, n, lbl in les["quizzes"]:
                bar = quiz_bar([("index.html", "← กลับไปอ่านสรุป"), ("../index.html", code), ("../../index.html", "หน้าแรก")])
                (ldir / n).write_text(inject_quiz(les[key].read_text(encoding="utf-8"), bar, 2), encoding="utf-8")

            search_index.append({"s": subj["code"], "t": short_title(les["title"]), "l": les["label"],
                                 "u": f"{subj['slug']}/{les['slug']}/index.html",
                                 "h": [[a, topic(t)] for a, t in les["toc"]]})
            for a in les["anims"]:
                bar = ext_bar([("index.html", f"← กลับไปอ่านสรุป {esc(les['label'])}"), ("../index.html", code), ("../../index.html", "หน้าแรก")])
                (ldir / a["name"]).write_text(inject_bar(a["html"], bar), encoding="utf-8")
                search_index.append({"s": subj["code"], "t": "🎬 " + a["title"],
                                     "u": f"{subj['slug']}/{les['slug']}/{a['name']}", "h": a["heads"]})

        reviews = find_reviews(subj)
        anim_pages = find_reviews(subj, "Animation-")
        quizpages = find_reviews(subj, "Quiz-")  # quizzes not tied to a summary
        for qp in quizpages:
            qdir = sdir / qp["slug"]
            qdir.mkdir(parents=True, exist_ok=True)
            bar = quiz_bar([("../index.html", f"← {code}"), ("../../index.html", "หน้าแรก")])
            q2files = sorted((subj["dir"] / qp["label"]).glob("quiz2-*.html"))
            qp["quiz2"] = bool(q2files)
            for out_name, text in [("index.html", qp["html"])] + [("quiz2.html", f.read_text(encoding="utf-8")) for f in q2files[:1]]:
                (qdir / out_name).write_text(inject_quiz(text, bar, 2), encoding="utf-8")
            qp["title"] = re.sub(r"^(Quiz:\s*|ข้อสอบจริง\s*)", "", qp["title"])
            search_index.append({"s": subj["code"], "t": qp["title"], "u": f"{subj['slug']}/{qp['slug']}/index.html", "h": []})
        for rv in reviews + anim_pages:
            rdir = sdir / rv["slug"]
            rdir.mkdir(parents=True, exist_ok=True)
            bar = ext_bar([("../index.html", f"← {code}"), ("../../index.html", "หน้าแรก")])
            (rdir / "index.html").write_text(inject_bar(rv["html"], bar), encoding="utf-8")
            search_index.append({"s": subj["code"], "t": rv["title"], "u": f"{subj['slug']}/{rv['slug']}/index.html",
                                 "h": rv["heads"]})

        nq = sum(len(l["quizzes"]) for l in lessons) + sum(1 + qp["quiz2"] for qp in quizpages)
        sbody, sscripts = subject_page(subj, lessons, nq, reviews, anim_pages, quizpages)
        crumbs = f'<a href="../index.html">หน้าแรก</a><span>/</span><b>{esc(subj["code"])}</b>'
        (sdir / "index.html").write_text(page(f"{subj['code']} {subj['name']}", sbody, 1, subj["accent"],
                                              crumbs=crumbs, scripts=sscripts,
                                              after='<script src="../assets/subject.js"></script>'), encoding="utf-8")
        home_lessons[subj["slug"]] = [l["slug"] for l in lessons]
        meta = [f"{len(lessons)} บท" if lessons else f"{len(reviews)} รีวิว"] + ([f"{nq} แบบทดสอบ"] if nq else [])
        subject_cards.append(
            f'<a class="subject-card" href="{subj["slug"]}/index.html" style="--accent:{subj["accent"]}" data-subj="{subj["slug"]}">'
            f'<div class="sc-top"><span class="sc-icon">{subj["icon"]}</span><span class="code">{esc(subj["code"])}</span></div>'
            f'<h2>{esc(subj["name"])}</h2><p>{esc(subj["th"])}</p>'
            f'<div class="sc-meta">{" · ".join(meta)}</div>'
            f'<div class="sc-progress" hidden><div class="bar"><i></i></div><span></span></div></a>')

    home = f"""
<main class="wrap home">
  <section class="home-hero">
    <p class="kicker">🌿 Mahidol ICT · ปี 2</p>
    <h1>สรุปบทเรียน <em class="nw">อ่านง่าย</em> <span class="nw">ทวนเร็ว</span></h1>
    <p class="lede">อ่านฉบับเต็มเพื่อเข้าใจ ใช้สรุปสั้นทวนก่อนสอบ แล้วลองทำแบบทดสอบท้ายบท</p>
    <div class="search">
      <label class="searchbox big"><svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true"><circle cx="9" cy="9" r="6" fill="none" stroke="currentColor" stroke-width="2"/><path d="M14 14l4 4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg><input id="q" type="search" placeholder="ค้นหาหัวข้อทุกวิชา เช่น cache, VLAN, use case…" autocomplete="off"><kbd>/</kbd></label>
      <ul id="results"></ul>
    </div>
  </section>
  <a class="continue" id="cont" hidden><span class="continue-play">▶</span><span><small>อ่านต่อจากครั้งก่อน</small><strong id="contTitle"></strong></span></a>
  <h2 class="section-title">วิชาทั้งหมด</h2>
  <section class="subject-grid">{''.join(subject_cards)}</section>
</main>"""
    scripts = (f"<script>window.SEARCH_INDEX = {jsn(search_index)};window.SN_LESSONS = {jsn(home_lessons)};</script>")
    (OUT / "index.html").write_text(page("Study Notes · สรุปบทเรียน", home, 0, scripts=scripts), encoding="utf-8")
    print("built", sum(1 for _ in OUT.rglob("*.html")), "html files")


SUBJECT_SLUGS = {s["slug"] for s in SUBJECTS}

if __name__ == "__main__":
    build()
