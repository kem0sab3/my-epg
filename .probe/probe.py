import json, re, datetime, html as H, urllib.request, urllib.error, urllib.parse
def p(tag, obj): print("P|" + tag + "|" + json.dumps(obj, ensure_ascii=False)[:2500], flush=True)
HD = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
def get(u, data=None):
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers=HD, data=data), timeout=40) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read(400).decode("utf-8", "replace")
def parse(page):
    out = []
    for m in re.finditer(r"data-start-time='(\d+)' data-end-time='(\d+)'(.*?)(?=data-start-time=|\Z)", page, re.S):
        s, e, rest = int(m.group(1)), int(m.group(2)), m.group(3)
        t = re.search(r'aria-label="([^"]+)"', rest)
        out.append((datetime.datetime.utcfromtimestamp(s/1000).isoformat(), datetime.datetime.utcfromtimestamp(e/1000).isoformat(), H.unescape(t.group(1)) if t else None))
    return out
st, page = get("https://tbn.uk/tv-guide/")
items = parse(page)
p("today", {"n": len(items), "first": items[:3], "last": items[-2:]})
p("daylinks", sorted(set(re.findall(r'href="([^"]*tv-guide[^"]*)"', page)))[:20])
p("buttons", sorted(set(re.findall(r'data-(?:date|day)=["\']([^"\']+)', page)))[:20])
st, js = get("https://tbn.uk/content/plugins/tbnuk-scheduler/public/js/tbnuk-scheduler-public-tv-guide.js?ver=1.0.56")
p("js", re.sub(r"\s+", " ", js)[:2500])
nonce = re.search(r'"nonce":"([^"]+)"', page).group(1)
tom = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
for q in [f"?date={tom}", f"?day={tom}", f"{tom}/"]:
    st, pg = get("https://tbn.uk/tv-guide/" + q); it = parse(pg)
    p("try", {"q": q, "st": st, "n": len(it), "first": it[:1]})
