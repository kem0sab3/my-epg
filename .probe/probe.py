import json, urllib.request, urllib.error, datetime
def p(tag, obj): print("P|" + tag + "|" + json.dumps(obj, ensure_ascii=False)[:1200], flush=True)
def get(url, hdr=None):
    h = {"User-Agent": "Mozilla/5.0"}; h.update(hdr or {})
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=40) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read(300)
    except Exception as e:
        return None, str(e).encode()
d = datetime.date.today().strftime("%Y%m%d")
st, body = get(f"https://awk.epgsky.com/hawk/linear/schedule/{d}/1005")
try:
    j = json.loads(body); ev = j["schedule"][0]["events"]
    p("sky-times", {"st": st, "n": len(ev), "first": ev[:2]})
except Exception as e:
    p("sky-times", {"st": st, "err": str(e), "b": body[:200].decode("utf-8", "replace")})
for acc in ["*/*", "application/json, text/plain, */*", None]:
    hdr = {"x-device-country": "GB", "x-device-language": "en"}
    if acc: hdr["Accept"] = acc
    st, body = get("https://api.lgchannels.com/api/v1.0/schedulelist", hdr)
    txt = body[:400].decode("utf-8", "replace")
    p("lg", {"accept": acc, "st": st, "head": txt})
    if st == 200:
        j = json.loads(body)
        cats = j.get("categories") or []
        p("lg-cats", [(c.get("categoryName"), len(c.get("schedules") or [])) for c in cats])
        for c in cats:
            for ch in c.get("schedules") or []:
                p("lgch", {"cat": c.get("categoryName"), "id": ch.get("channelId"), "name": ch.get("channelName"),
                           "url": ch.get("mediaStaticUrl"), "logo": ch.get("channelLogoUrl"), "progs": len(ch.get("programs") or [])})
        break
