import json, urllib.request, urllib.error
def p(tag, obj): print("P|" + tag + "|" + json.dumps(obj, ensure_ascii=False)[:300], flush=True)
Q = "?direct=true&aw_0_1st.playerid=kem0sab3_epg&aw_0_1st.skey=1793860000"
urls = {
 "Clyde 1": "https://stream-al.hellorayo.co.uk/clyde1.aac", "Forth 1": "https://stream-al.hellorayo.co.uk/forth1.aac",
 "Northsound 1": "https://stream-mz.hellorayo.co.uk/northsound1.aac", "Tay FM": "https://stream-mz.hellorayo.co.uk/tayfm.aac",
 "MFR": "https://stream-mz.hellorayo.co.uk/mfrfm.aac",
 "GHR (apollo)": "https://stream.apollo.audio/gh0/hi/aac/", "Hits (apollo)": "https://stream.apollo.audio/hit/hi/aac/",
 "Magic (apollo)": "https://stream.apollo.audio/mag/hi/aac/", "Clyde (apollo)": "https://stream.apollo.audio/cl1/hi/aac/",
 "Absolute": "https://stream-ar.hellorayo.co.uk/absoluteradiohigh.aac", "Absolute 80s": "https://stream-ar.hellorayo.co.uk/absolute80shigh.aac",
 "Absolute 90s": "https://stream-ar.hellorayo.co.uk/absolute90shigh.aac", "KISS": "https://live-bauerkiss.sharp-stream.com/kissnational.aac",
 "KISSTORY": "https://live-bauerkiss.sharp-stream.com/kisstory.aac", "Jazz FM": "https://stream-al.hellorayo.co.uk/jazzhigh.aac",
 "Kerrang": "https://stream-al.hellorayo.co.uk/kerrang.aac", "Planet Rock": "https://stream-mz.hellorayo.co.uk/planetrock.aac",
}
for name, base in urls.items():
    u = base + Q
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=20) as r:
            p("s", {"name": name, "st": r.status, "ct": r.headers.get("Content-Type"), "final": r.geturl().split("?")[0], "n": len(r.read(2000))})
    except urllib.error.HTTPError as e:
        p("s", {"name": name, "st": e.code})
    except Exception as e:
        p("s", {"name": name, "err": str(e)[:80]})
