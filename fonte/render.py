"""Gera as artes dos posts do @renato.dodp a partir de fonte/posts.json.

Uso: python3 fonte/render.py [id ...]
Saída: posts/<data>-<id>/ com slide-NN.jpg (feed 1080x1350), reel.mp4 + capa.jpg (Reels 1080x1920)
e legenda.txt. Também atualiza calendario.json na raiz do repositório.
"""
import json, os, subprocess, sys, tempfile
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = "https://raw.githubusercontent.com/renatorenov/renovdp-midia/main/"
CDN = "https://cdn.jsdelivr.net/gh/renatorenov/renovdp-midia@main/"
HANDLE = "@renato.dodp"

BG, INK, MUTED, ACCENT, LINE, DIM = "#0E1B2C", "#F3F1EC", "#C9D1DB", "#3FCB7E", "#2A3C52", "#8A97A8"

def css(w, h, scale):
    s = lambda v: f"{round(v * scale)}px"
    return f"""
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{w}px;height:{h}px}}
body{{background:{BG};color:{INK};font-family:'Inter',sans-serif;position:relative;overflow:hidden}}
.bar{{position:absolute;left:96px;top:0;width:120px;height:14px;background:{ACCENT}}}
.kicker{{font-family:'Poppins';font-weight:600;font-size:{s(30)};letter-spacing:4px;text-transform:uppercase;color:{ACCENT}}}
h1{{font-family:'Poppins';font-weight:700;font-size:{s(84)};line-height:1.08;margin-top:{s(52)};letter-spacing:-1px}}
h2{{font-family:'Poppins';font-weight:700;font-size:{s(74)};line-height:1.1;letter-spacing:-1px;margin-top:{s(28)}}}
em{{font-style:normal;color:{ACCENT}}}
.num{{font-family:'Poppins';font-weight:700;font-size:{s(200)};line-height:1;color:{ACCENT}}}
p{{font-size:{s(42)};line-height:1.45;color:{MUTED};margin-top:{s(48)};max-width:880px}}
.extra{{font-size:{s(38)};line-height:1.45;color:{INK};margin-top:{s(64)};padding-top:{s(44)};border-top:2px solid {LINE}}}
.foot{{position:absolute;left:96px;right:96px;bottom:{s(70)};display:flex;justify-content:space-between;font-size:{s(30)};color:{DIM};font-weight:500}}
.foot b{{color:{INK};font-weight:600}}
.swipe{{color:{ACCENT};font-weight:600}}
.center{{position:absolute;left:96px;right:96px;top:50%;transform:translateY(-55%)}}
.cta h2{{font-size:{s(88)};margin-top:{s(40)}}}
.cta p{{color:{ACCENT};font-weight:600}}
ul{{list-style:none;margin-top:{s(56)}}}
li{{font-size:{s(40)};line-height:1.3;padding:{s(26)} 0 {s(26)} {s(70)};border-top:2px solid {LINE};position:relative;color:{INK}}}
li:last-child{{border-bottom:2px solid {LINE}}}
li:before{{content:'';position:absolute;left:0;top:50%;width:{s(36)};height:{s(36)};margin-top:-{s(18)};border:4px solid {ACCENT};border-radius:8px}}
li:after{{content:'';position:absolute;left:{s(11)};top:50%;width:{s(12)};height:{s(22)};margin-top:-{s(16)};border:solid {ACCENT};border-width:0 5px 5px 0;transform:rotate(45deg)}}
.hook h1{{font-size:{s(96)};margin-top:0}}
"""

def body(slide, foot_right):
    t = slide["t"]
    if t == "cover":
        inner = f'<div class="kicker">{slide["kicker"]}</div><h1>{slide["title"]}</h1><p>{slide["body"]}</p>'
    elif t == "item":
        inner = f'<div class="num">{slide["n"]}</div><h2>{slide["title"]}</h2><p>{slide["body"]}</p>'
    elif t == "cta":
        extra = f'<div class="extra">{slide["extra"]}</div>' if slide.get("extra") else ""
        kicker = '<div class="kicker">Agora é com você</div>' if slide.get("extra") else ""
        inner = f'<div class="cta">{kicker}<h2>{slide["title"]}</h2><p>{slide["body"]}</p>{extra}</div>'
    elif t == "statement":
        inner = f'<div class="kicker">{slide["kicker"]}</div><h1>{slide["title"]}</h1><p>{slide["body"]}</p>'
    elif t == "check":
        items = "".join(f"<li>{i}</li>" for i in slide["items"])
        inner = f'<div class="kicker">{slide["kicker"]}</div><h2>{slide["title"]}</h2><ul>{items}</ul>'
    elif t == "hook":
        inner = f'<div class="hook"><h1>{slide["title"]}</h1></div>'
    else:
        raise ValueError(t)
    foot = f'<div class="foot"><b>{HANDLE}</b><span>{foot_right}</span></div>'
    return f'<div class="bar"></div><div class="center">{inner}</div>{foot}'

def page(w, h, scale, content):
    return f'<html><head><meta charset="utf-8"><style>{css(w, h, scale)}</style></head><body>{content}</body></html>'

def shoot(pg, html, path, w, h, kind="jpeg"):
    pg.set_viewport_size({"width": w, "height": h})
    pg.set_content(html)
    pg.wait_for_timeout(120)
    # trava se algum texto vazar da área útil
    overflow = pg.evaluate("""() => { const c=document.querySelector('.center'); const f=document.querySelector('.foot');
        const r=c.getBoundingClientRect(); return r.top < 40 || r.bottom > f.getBoundingClientRect().top - 30; }""")
    if overflow:
        raise SystemExit(f"Texto não cabe: {path}")
    if kind == "jpeg":
        pg.screenshot(path=path, type="jpeg", quality=92)
    else:
        pg.screenshot(path=path, type="png")

def make_reel(pg, frames, outdir):
    W, H, SC = 1080, 1920, 1.12
    tmp = tempfile.mkdtemp()
    pngs = []
    for i, f in enumerate(frames, 1):
        right = "Assista até o fim" if i == 1 else f"{i}/{len(frames)}"
        p = os.path.join(tmp, f"f{i:02d}.png")
        shoot(pg, page(W, H, SC, body(f, right)), p, W, H, "png")
        pngs.append(p)
    # capa (também usada no feed)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", pngs[0], "-q:v", "2", os.path.join(outdir, "capa.jpg")], check=True)
    dur, fade = 3.6, 0.5
    durs = [dur + 1.2 if i == len(pngs) - 1 else dur for i in range(len(pngs))]
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    for p, d in zip(pngs, durs):
        cmd += ["-loop", "1", "-t", f"{d}", "-framerate", "30", "-i", p]
    total = sum(durs) - fade * (len(pngs) - 1)
    cmd += ["-f", "lavfi", "-t", f"{total}", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]
    chain, last, offset = [], "[0:v]", 0.0
    for i in range(1, len(pngs)):
        offset += durs[i - 1] - fade
        out = f"[v{i}]"
        chain.append(f"{last}[{i}:v]xfade=transition=fade:duration={fade}:offset={offset:.2f}{out}")
        last = out
    chain.append(f"{last}format=yuv420p[vout]")
    cmd += ["-filter_complex", ";".join(chain), "-map", "[vout]", "-map", f"{len(pngs)}:a",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-r", "30", "-c:a", "aac", "-b:a", "128k",
            "-shortest", "-movflags", "+faststart", os.path.join(outdir, "reel.mp4")]
    subprocess.run(cmd, check=True)

def main():
    posts = json.load(open(os.path.join(ROOT, "fonte", "posts.json")))
    only = set(sys.argv[1:])
    cal = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        for post in posts:
            folder = f"posts/{post['date']}-{post['id']}"
            outdir = os.path.join(ROOT, folder)
            if not only or post["id"] in only:
                os.makedirs(outdir, exist_ok=True)
                if post["type"] == "carousel":
                    n = len(post["slides"])
                    for i, s in enumerate(post["slides"], 1):
                        right = '<span class="swipe">Arraste →</span>' if i == 1 else f"{i}/{n}"
                        shoot(pg, page(1080, 1350, 1.0, body(s, right)), os.path.join(outdir, f"slide-{i:02d}.jpg"), 1080, 1350)
                elif post["type"] == "single":
                    shoot(pg, page(1080, 1350, 1.0, body(post["slide"], "")), os.path.join(outdir, "slide-01.jpg"), 1080, 1350)
                elif post["type"] == "reel":
                    make_reel(pg, post["frames"], outdir)
                open(os.path.join(outdir, "legenda.txt"), "w").write(post["caption"] + "\n")
                print("ok", folder)
            entry = {"id": post["id"], "date": post["date"], "type": post["type"], "tema": post["tema"], "caption": post["caption"]}
            if post["type"] == "carousel":
                entry["image_urls"] = [f"{RAW}{folder}/slide-{i:02d}.jpg" for i in range(1, len(post["slides"]) + 1)]
            elif post["type"] == "single":
                entry["image_url"] = f"{RAW}{folder}/slide-01.jpg"
            else:
                entry["video_url"] = f"{CDN}{folder}/reel.mp4"
                entry["cover_url"] = f"{RAW}{folder}/capa.jpg"
            cal.append(entry)
        b.close()
    json.dump({"conta": "renato.dodp", "instagram_account_id": "17841442704877427", "posts": cal},
              open(os.path.join(ROOT, "calendario.json"), "w"), ensure_ascii=False, indent=1)
    print("calendario.json:", len(cal), "posts")

if __name__ == "__main__":
    main()
