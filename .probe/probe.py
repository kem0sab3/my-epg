import json, datetime, urllib.request, urllib.error, urllib.parse
def p(tag, obj): print("P|" + tag + "|" + json.dumps(obj, ensure_ascii=False)[:3000], flush=True)
HD = {"User-Agent": "Mozilla/5.0", "Accept": "application/json, */*", "Origin": "https://islamchannel.tv", "Referer": "https://islamchannel.tv/",
      "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
for d in range(0, 9):
    date = (datetime.date.today() + datetime.timedelta(days=d)).isoformat()
    data = urllib.parse.urlencode({"channel_id": 4, "date": date}).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request("https://epg.etechnologies.com.tr/v1/api/dailySchedules/day-guide", data=data, headers=HD), timeout=40) as r:
            j = json.load(r)
        det = j.get("epg_details") or []
        p("day", {"date": date, "avail": j.get("epg_available"), "keys": sorted(j.keys()), "n": len(det),
                  "first": det[:2] if d == 0 else [(x.get("start_time"), x.get("title") or x.get("program_name")) for x in det[:2]], "last": det[-1:] if d == 0 else None})
    except urllib.error.HTTPError as e:
        p("day", {"date": date, "st": e.code, "b": e.read(300).decode("utf-8", "replace")})
    except Exception as e:
        p("day", {"date": date, "err": str(e)[:100]})
