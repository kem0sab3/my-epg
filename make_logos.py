#!/usr/bin/env python3
"""Downloads channel logos from Wikipedia, turns them white for dark TV app backgrounds,
and saves them in logos/. The list is in logos.txt: one line per logo, 'file-name | Wikipedia article'.
'file-name | crest:Wikipedia article' keeps the colours (football club crests); 'crest-white:' turns the crest white."""
import io, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request
from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "my-epg-logo-fetcher/1.0 (personal TV playlist; github.com/kem0sab3/my-epg)"}

def get(url):
    for attempt in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 4:
                raise
            time.sleep(10 * (attempt + 1))   # Wikipedia asked us to slow down

def crest(article):
    """A club's current crest, in colour: the image in its Wikipedia infobox, rendered as a PNG."""
    q = urllib.parse.urlencode({"action": "query", "format": "json", "prop": "revisions", "rvprop": "content", "rvslots": "main",
                                "rvsection": 0, "redirects": 1, "titles": article})
    page = next(iter(json.loads(get("https://en.wikipedia.org/w/api.php?" + q))["query"]["pages"].values()))
    text = page["revisions"][0]["slots"]["main"]["*"]
    m = re.search(r"\|\s*(?:image|logo|badge|crest)\s*=\s*(?:\[\[)?(?:File:|Image:)?([^|\]\n]+\.(?:svg|png))", text, re.I)
    if not m:
        return None, None
    f = "File:" + m.group(1).strip()
    q = urllib.parse.urlencode({"action": "query", "format": "json", "prop": "imageinfo", "iiprop": "url", "iiurlwidth": 800, "titles": f})
    info = next(iter(json.loads(get("https://en.wikipedia.org/w/api.php?" + q))["query"]["pages"].values()))
    ii = (info.get("imageinfo") or [{}])[0]
    return f, ii.get("thumburl") or ii.get("url")

def logo_url(article):
    q = urllib.parse.urlencode({"action": "query", "format": "json", "prop": "pageimages", "piprop": "thumbnail|name",
                                "pithumbsize": 1200, "redirects": 1, "titles": article})
    pages = json.loads(get("https://en.wikipedia.org/w/api.php?" + q))["query"]["pages"]
    page = next(iter(pages.values()))
    return page.get("pageimage"), (page.get("thumbnail") or {}).get("source")

def logo_from_article_files(article):
    """Fallback: look through the article's image files for one named after the station (works for non-free logos too)."""
    q = urllib.parse.urlencode({"action": "query", "format": "json", "prop": "images", "imlimit": 50, "redirects": 1, "titles": article})
    pages = json.loads(get("https://en.wikipedia.org/w/api.php?" + q))["query"]["pages"]
    files = [i["title"] for p in pages.values() for i in p.get("images", [])]
    words = [w.lower() for w in article.replace("BBC", "").replace("Radio", "").split() if len(w) > 1]
    cands = [f for f in files if f.lower().endswith((".svg", ".png")) and all(w in f.lower() for w in words)]
    for f in cands:
        q = urllib.parse.urlencode({"action": "query", "format": "json", "prop": "imageinfo", "iiprop": "url",
                                    "iiurlwidth": 1200, "titles": f})
        info = next(iter(json.loads(get("https://en.wikipedia.org/w/api.php?" + q))["query"]["pages"].values()))
        ii = (info.get("imageinfo") or [{}])[0]
        url = ii.get("thumburl") or ii.get("url")
        if url:
            return f, url
    return None, None

def is_dark(im):
    """True when the visible part of a logo is mostly dark (would vanish on a dark TV background)."""
    a = im.getchannel("A"); L = im.convert("L")
    px = [l for l, al in zip(L.getdata(), a.getdata()) if al > 128]
    return bool(px) and sum(px) / len(px) < 110

def tile_lettering(data):
    """For logos drawn as white lettering on a grey/coloured tile (with a white margin around it):
    keep only the lettering, in white, and drop the tile and the margin."""
    im = Image.open(io.BytesIO(data)).convert("RGBA")
    flat = Image.new("RGBA", im.size, (255, 255, 255, 255)); flat.alpha_composite(im)
    L = flat.convert("L")
    light = L.point(lambda v: 255 if v > 200 else 0)
    w, h = light.size
    for xy in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        if light.getpixel(xy) == 255:
            ImageDraw.floodfill(light, xy, 128)          # 128 = margin connected to the edge
    margin = light.point(lambda v: 255 if v == 128 else 0).filter(ImageFilter.MaxFilter(5))
    inside = ImageChops.invert(margin)
    alpha = ImageChops.multiply(L.point(lambda v: max(0, min(255, int((v - 150) * 255 / 90)))), inside)
    out = Image.new("RGBA", im.size, (255, 255, 255, 0)); out.putalpha(alpha)
    box = alpha.getbbox()
    return out.crop(box) if box else out

def whiten(data, only_if_dark=False):
    im = Image.open(io.BytesIO(data)).convert("RGBA")
    if only_if_dark and im.getchannel("A").getextrema()[0] < 250 and not is_dark(im):
        box = im.getchannel("A").getbbox()
        return im.crop(box) if box else im
    a = im.getchannel("A")
    if a.getextrema()[0] < 250:      # has a see-through background: make every visible pixel white
        alpha = a
    else:                            # solid background: dark ink becomes white, light background becomes see-through
        alpha = Image.eval(im.convert("L"), lambda v: 255 - v)
    out = Image.new("RGBA", im.size, (255, 255, 255, 0))
    out.putalpha(alpha)
    box = alpha.getbbox()
    return out.crop(box) if box else out

def main():
    os.makedirs(os.path.join(HERE, "logos"), exist_ok=True)
    for line in open(os.path.join(HERE, "logos.txt"), encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "|" not in line:
            continue
        name, article = [x.strip() for x in line.split("|", 1)]
        time.sleep(1)
        try:
            if article.startswith(("crest:", "crest-white:")):
                fname, url = crest(article.split(":", 1)[1].strip())
                if not url:
                    print(f"!! {article}: no crest in the Wikipedia infobox"); continue
                data = get(url)
                img = Image.open(io.BytesIO(data)).convert("RGBA")
                if article.startswith("crest-white:"):   # for dark one-colour crests that vanish on a dark background
                    img = whiten(data)
                box = img.getchannel("A").getbbox()
                img = img.crop(box) if box else img
                img.thumbnail((600, 600))
                img.save(os.path.join(HERE, "logos", name + ".png"), optimize=True)
                print(f"ok {name}.png  <- {article} ({fname}) {img.size}")
                continue
            if article.startswith(("url:", "tile:", "raw:", "white:")):
                mode, url = article.split(":", 1)
                fname, url = "direct", url.strip()
                if mode == "tile":
                    img = tile_lettering(get(url))
                elif mode == "white":
                    img = whiten(get(url))
                elif mode == "raw":
                    img = Image.open(io.BytesIO(get(url))).convert("RGBA")
                else:
                    img = whiten(get(url), only_if_dark=True)
                img.thumbnail((1200, 1200))
                img.save(os.path.join(HERE, "logos", name + ".png"), optimize=True)
                print(f"ok {name}.png  <- {url} {img.size}")
                continue
            fname, url = logo_url(article)
            if not url:
                fname, url = logo_from_article_files(article)
            if not url:
                print(f"!! {article}: no logo image on Wikipedia"); continue
            img = whiten(get(url))
            img.thumbnail((1200, 1200))
            img.save(os.path.join(HERE, "logos", name + ".png"), optimize=True)
            print(f"ok {name}.png  <- {article} ({fname}) {img.size}")
        except Exception as e:
            print(f"!! {article}: {e}")

if __name__ == "__main__":
    main()
