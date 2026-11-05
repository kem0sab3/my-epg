#!/usr/bin/env python3
"""Downloads channel logos from Wikipedia, turns them white for dark TV app backgrounds,
and saves them in logos/. The list is in logos.txt: one line per logo, 'file-name | Wikipedia article'."""
import io, json, os, sys, urllib.parse, urllib.request
from PIL import Image, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "my-epg-logo-fetcher/1.0 (personal TV playlist; github.com/kem0sab3/my-epg)"}

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()

def logo_url(article):
    q = urllib.parse.urlencode({"action": "query", "format": "json", "prop": "pageimages", "piprop": "thumbnail|name",
                                "pithumbsize": 1200, "redirects": 1, "titles": article})
    pages = json.loads(get("https://en.wikipedia.org/w/api.php?" + q))["query"]["pages"]
    page = next(iter(pages.values()))
    return page.get("pageimage"), (page.get("thumbnail") or {}).get("source")

def whiten(data):
    im = Image.open(io.BytesIO(data)).convert("RGBA")
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
        try:
            fname, url = logo_url(article)
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
