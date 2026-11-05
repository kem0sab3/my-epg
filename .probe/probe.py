import json, re, urllib.request
def p(tag, obj): print("P|" + tag + "|" + json.dumps(obj, ensure_ascii=False)[:3500], flush=True)
HD = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
def get(u):
    with urllib.request.urlopen(urllib.request.Request(u, headers=HD), timeout=40) as r:
        return r.read().decode("utf-8", "replace")
page = get("https://tbn.uk/tv-guide/2026-11-06/")
i = page.find("data-start-time=")
j = page.find("data-start-time=", i + 20)
p("block", re.sub(r"\s+", " ", page[i:j]))
links = sorted(set(re.findall(r'href="(https://tbn.uk/tv/[^"]+)"', page)))
p("links", {"n": len(links), "sample": links[:5]})
for u in links[:3]:
    h = get(u)
    p("prog", {"u": u, "og": (re.search(r'<meta property="og:description" content="([^"]*)"', h) or [0, None])[1],
               "meta": (re.search(r'<meta name="description" content="([^"]*)"', h) or [0, None])[1],
               "body": re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", (re.search(r'<main.*?</main>', h, re.S) or [""])[0]))[:600]})
