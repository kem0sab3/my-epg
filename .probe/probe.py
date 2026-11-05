import json, re, datetime, urllib.request, urllib.error
def p(tag, obj): print("P|" + tag + "|" + json.dumps(obj, ensure_ascii=False)[:1500], flush=True)
H = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
def get(u):
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=30) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read(300).decode("utf-8", "replace")
    except Exception as e:
        return None, str(e)
d = datetime.date.today().isoformat()
for sid in ["bbc_arabic_tv", "bbc_persian_tv", "bbc_pashto_tv", "bbc_arabic", "bbc_persian", "bbc_pashto"]:
    for u in [f"https://ess.api.bbci.co.uk/schedules?serviceId={sid}",
              f"https://rms.api.bbc.co.uk/v2/experience/inline/schedules/{sid}/{d}",
              f"https://ibl.api.bbci.co.uk/ibl/v1/channels/{sid}/schedule/{d}"]:
        st, b = get(u)
        n = len(re.findall(r'"(?:start|scheduled_start|published_time)"', b))
        p("try", {"u": u, "st": st, "starts": n, "head": b[:220]})
