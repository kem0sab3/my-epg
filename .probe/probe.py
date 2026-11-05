import json, time, urllib.request, urllib.error
def p(tag, obj): print("P|" + tag + "|" + json.dumps(obj, ensure_ascii=False)[:300], flush=True)
def test(u):
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=20) as r:
            return r.status, len(r.read(2000))
    except urllib.error.HTTPError as e:
        return e.code, 0
    except Exception as e:
        return str(e)[:50], 0
now = int(time.time())
base = "https://stream-al.hellorayo.co.uk/clyde1.aac"
for label, skey in [("current-link (fixed old)", 1793860000), ("now", now), ("now+1h", now + 3600), ("now+1day", now + 86400),
                    ("far future", 7374499933), ("now-1h", now - 3600), ("now-6h", now - 6 * 3600), ("now-12h", now - 12 * 3600)]:
    st, n = test(f"{base}?direct=true&aw_0_1st.playerid=kem0sab3_epg&aw_0_1st.skey={skey}")
    p("skey", {"label": label, "skey": skey, "st": st, "bytes": n})
for name, u in [("Forth 1", "https://stream-al.hellorayo.co.uk/forth1.aac"), ("KISS", "https://live-bauerkiss.sharp-stream.com/kissnational.aac"),
                ("Planet Rock", "https://stream-mz.hellorayo.co.uk/planetrock.aac")]:
    for label, skey in [("old", 1793860000), ("far future", 7374499933)]:
        st, n = test(f"{u}?direct=true&aw_0_1st.playerid=kem0sab3_epg&aw_0_1st.skey={skey}")
        p("other", {"name": name, "label": label, "st": st, "bytes": n})
