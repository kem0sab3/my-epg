import json, time, urllib.request, urllib.error
def p(tag, obj): print("P|" + tag + "|" + json.dumps(obj, ensure_ascii=False)[:300], flush=True)
def test(u):
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=20) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
now = int(time.time())
base = "https://stream-al.hellorayo.co.uk/clyde1.aac?direct=true&aw_0_1st.playerid=kem0sab3_epg&aw_0_1st.skey="
for label, skey in [("+2h", now+7200), ("+4h", now+4*3600), ("+8h", now+8*3600), ("-8h", now-8*3600), ("-10h", now-10*3600),
                    ("2030", 1893456000), ("2050", 2524608000), ("2100", 4102444800), ("7374499933", 7374499933), ("9999999999", 9999999999),
                    ("12345", 12345), ("abc", "abc"), ("13-digit ms now", now*1000)]:
    p("skey", {"label": label, "st": test(base + str(skey))})
