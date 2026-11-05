import json, urllib.request, urllib.error, time
def p(tag, obj): print("P|" + tag + "|" + json.dumps(obj, ensure_ascii=False)[:300], flush=True)
def fetch(u):
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=20) as r:
            return r.status, r.headers.get("Content-Type"), len(r.read(1000))
    except urllib.error.HTTPError as e:
        return e.code, None, 0
    except Exception as e:
        return str(e)[:60], None, 0
now = int(time.time())
for pid in ["BMUK_inpage_html5", "BMUK_html5", "BMUK_Web", "BMUK_RPH5", "BMUK_Rayo", "BMUK_rayo_web"]:
    for q in [f"?direct=true&aw_0_1st.playerid={pid}", f"?direct=true&aw_0_1st.playerid={pid}&aw_0_1st.skey={now}"]:
        u = "https://stream-al.hellorayo.co.uk/clyde1.aac" + q
        st, ct, n = fetch(u); p("pid", {"q": q, "st": st, "ct": ct, "n": n})
# also the apollo redirector used by Bauer's own apps, with the web player id
for q in ["?direct=true&aw_0_1st.playerid=BMUK_inpage_html5", "?direct=false&aw_0_1st.playerid=BMUK_inpage_html5"]:
    u = "https://stream.apollo.audio/cl1/hi/aac/" + q
    st, ct, n = fetch(u); p("apollo", {"q": q, "st": st, "ct": ct, "n": n})
