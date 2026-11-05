import json, re, datetime, urllib.request, urllib.error
def p(tag, obj): print("P|" + tag + "|" + json.dumps(obj, ensure_ascii=False)[:3500], flush=True)
HD = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
      "Accept": "application/json, text/plain, */*", "Origin": "https://islamchannel.tv", "Referer": "https://islamchannel.tv/"}
def get(u, hdr=HD):
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers=hdr), timeout=40) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read(500).decode("utf-8", "replace")
st, html = get("https://islamchannel.tv/tv-guide/", {"User-Agent": HD["User-Agent"]})
i = html.find("etechnologies")
p("ctx", re.sub(r"\s+", " ", html[max(0, i-2500):i+2500]))
