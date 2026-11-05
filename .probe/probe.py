import json, re, urllib.request, urllib.error
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
def get(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=40) as r:
            return r.status, r.read().decode("utf-8", "replace"), r.geturl()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace"), url
def p(tag, obj): print("P|" + tag + "|" + json.dumps(obj, ensure_ascii=False)[:3000], flush=True)
for u in ["https://hellorayo.co.uk/clyde-1/schedule/", "https://planetradio.co.uk/clyde/schedule/", "https://hellorayo.co.uk/clyde-1/schedule"]:
    st, html, final = get(u)
    p("page", {"u": u, "status": st, "final": final, "len": len(html)})
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if m:
        data = json.loads(m.group(1))
        # find schedule-like lists
        found = []
        def walk(n, path):
            if isinstance(n, dict):
                ks = set(n.keys())
                if ({"start", "end"} <= ks or {"startTime", "endTime"} <= ks or {"showStartTime"} <= ks or {"episodeStart"} <= ks) and len(found) < 4:
                    found.append({"path": path, "item": n})
                for k, v in n.items(): walk(v, path + "/" + k)
            elif isinstance(n, list):
                for i, v in enumerate(n[:200]): walk(v, path + f"[{i}]")
        walk(data, "")
        p("next", {"u": u, "found": found})
        p("next-pageprops-keys", sorted((data.get("props", {}).get("pageProps") or {}).keys())[:50])
    else:
        api = sorted(set(re.findall(r'https?://[a-z0-9.-]*(?:api|listen)[a-z0-9.-]*/[^"\'\s<>]{0,120}', html)))[:30]
        p("no-next", {"u": u, "apis": api, "snippet": re.sub(r"\s+", " ", html[:1500])})
    if st == 200: break
