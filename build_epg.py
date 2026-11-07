#!/usr/bin/env python3
"""Builds epg.xml.gz from the links in sources.txt.
Run by GitHub every day (see .github/workflows/update-epg.yml).
You shouldn't need to edit this file - change sources.txt / channels.txt / settings.txt instead."""
import datetime, gzip, os, re, shutil, sys, tempfile, urllib.parse, urllib.request
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))

def read_list(name):
    path = os.path.join(HERE, name)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip() and not l.strip().startswith("#")]

def read_settings():
    s = {"name": "My EPG", "days_ahead": "7"}
    for line in read_list("settings.txt"):
        if "=" in line:
            k, v = line.split("=", 1)
            s[k.strip()] = v.strip()
    return s

def parse_time(t):
    t = (t or "").strip()
    try:
        if " " in t:
            d, tz = t.split(" ", 1)
            return datetime.datetime.strptime(d[:14] + tz.strip(), "%Y%m%d%H%M%S%z")
        return datetime.datetime.strptime(t[:14], "%Y%m%d%H%M%S").replace(tzinfo=datetime.timezone.utc)
    except ValueError:
        return None

BBC_SCHEDULE = "https://rms.api.bbc.co.uk/v2/experience/inline/schedules/{station}/{date}"

def _find_broadcasts(node, found):
    """Walk the BBC's schedule JSON and collect anything that looks like a broadcast."""
    if isinstance(node, dict):
        start = node.get("start") or (node.get("published_time") or {}).get("start")
        end = node.get("end") or (node.get("published_time") or {}).get("end")
        titles = node.get("titles") if isinstance(node.get("titles"), dict) else None
        if start and end and titles:
            found.append(node)
        for v in node.values():
            _find_broadcasts(v, found)
    elif isinstance(node, list):
        for v in node:
            _find_broadcasts(v, found)

def _xmltv_time(iso):
    d = datetime.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return d.astimezone(datetime.timezone.utc).strftime("%Y%m%d%H%M%S +0000")

def grab_bbc_radio(stations, days, out_path):
    """Build an XMLTV file from the BBC's own radio schedules (the data BBC Sounds uses)."""
    import json
    tv = ET.Element("tv")
    today = datetime.datetime.now(datetime.timezone.utc).date()
    total = 0
    for station in stations:
        ch = ET.SubElement(tv, "channel", id=station)
        ET.SubElement(ch, "display-name").text = station
        seen, n = set(), 0
        for day in range(-1, days):
            url = BBC_SCHEDULE.format(station=station, date=(today + datetime.timedelta(days=day)).isoformat())
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
                with urllib.request.urlopen(req, timeout=30) as r:
                    data = json.load(r)
            except Exception as e:
                if day == 0:
                    print(f"   !! {station}: {e}", flush=True)
                continue
            items = []
            _find_broadcasts(data, items)
            for it in items:
                start = it.get("start") or it["published_time"]["start"]
                end = it.get("end") or it["published_time"]["end"]
                if start in seen:
                    continue
                seen.add(start)
                t = it["titles"]
                p = ET.SubElement(tv, "programme", start=_xmltv_time(start), stop=_xmltv_time(end), channel=station)
                ET.SubElement(p, "title").text = t.get("primary") or station
                if t.get("secondary"):
                    ET.SubElement(p, "sub-title").text = t["secondary"]
                syn = it.get("synopses") or {}
                desc = syn.get("medium") or syn.get("short") or syn.get("long")
                if desc:
                    ET.SubElement(p, "desc").text = desc
                n += 1
        total += n
    ET.ElementTree(tv).write(out_path, encoding="utf-8", xml_declaration=True)
    print(f"   BBC radio schedules: {total} programmes for {len(stations)} stations", flush=True)
    return out_path

def _get_json(url):
    import json
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)

def grab_bauer(stations, days, out_path):
    """Radio schedules for Bauer (Rayo) stations: Clyde 1, Forth 1, Greatest Hits Radio, KISS, Magic, Absolute..."""
    tv = ET.Element("tv")
    total = 0
    for code in stations:
        ch = ET.SubElement(tv, "channel", id=f"bauer-{code}")
        ET.SubElement(ch, "display-name").text = code
        try:
            data = _get_json(f"https://listenapi.planetradio.co.uk/api9.2/schedule/{code}/today/%2B{int(days)}%20days")
        except Exception as e:
            print(f"   !! bauer {code}: {e}", flush=True)
            continue
        if not isinstance(data, dict):
            continue
        seen = set()
        for day in data.values():
            for it in day if isinstance(day, list) else []:
                try:
                    start = datetime.datetime.fromisoformat(it["start"])
                    stop = start + datetime.timedelta(seconds=int(it.get("duration") or 3600))
                except Exception:
                    continue
                if it["start"] in seen:
                    continue
                seen.add(it["start"])
                p = ET.SubElement(tv, "programme", start=start.astimezone(datetime.timezone.utc).strftime("%Y%m%d%H%M%S +0000"),
                                  stop=stop.astimezone(datetime.timezone.utc).strftime("%Y%m%d%H%M%S +0000"), channel=f"bauer-{code}")
                ET.SubElement(p, "title").text = it.get("title") or code
                if it.get("shortdesc"):
                    ET.SubElement(p, "desc").text = it["shortdesc"]
                if it.get("image_url"):
                    ET.SubElement(p, "icon", src=it["image_url"])
                total += 1
    ET.ElementTree(tv).write(out_path, encoding="utf-8", xml_declaration=True)
    print(f"   Bauer radio schedules: {total} programmes for {len(stations)} stations", flush=True)
    return out_path

def grab_sky(services, days, out_path):
    """Listings from Sky's TV guide, by Sky service number (e.g. 1005 = Times Radio)."""
    tv = ET.Element("tv")
    total = 0
    today = datetime.datetime.now(datetime.timezone.utc).date()
    for sid in services:
        ch = ET.SubElement(tv, "channel", id=f"sky-{sid}")
        ET.SubElement(ch, "display-name").text = sid
        for d in range(int(days)):
            date = (today + datetime.timedelta(days=d)).strftime("%Y%m%d")
            try:
                j = _get_json(f"https://awk.epgsky.com/hawk/linear/schedule/{date}/{sid}")
                events = (j.get("schedule") or [{}])[0].get("events") or []
            except Exception as e:
                if d == 0:
                    print(f"   !! sky {sid}: {e}", flush=True)
                continue
            for ev in events:
                try:
                    start = datetime.datetime.fromtimestamp(int(ev["st"]), datetime.timezone.utc)
                    stop = start + datetime.timedelta(seconds=int(ev["d"]))
                except Exception:
                    continue
                p = ET.SubElement(tv, "programme", start=start.strftime("%Y%m%d%H%M%S +0000"),
                                  stop=stop.strftime("%Y%m%d%H%M%S +0000"), channel=f"sky-{sid}")
                ET.SubElement(p, "title").text = ev.get("t") or sid
                if ev.get("sy"):
                    ET.SubElement(p, "desc").text = ev["sy"]
                total += 1
    ET.ElementTree(tv).write(out_path, encoding="utf-8", xml_declaration=True)
    print(f"   Sky guide: {total} programmes for {len(services)} channels", flush=True)
    return out_path

def grab_rakuten_uk(days, out_path):
    """Listings for Rakuten TV's free UK channels, from Rakuten's own channel guide."""
    now = datetime.datetime.now(datetime.timezone.utc).replace(minute=0, second=0, microsecond=0)
    end = now + datetime.timedelta(days=min(int(days), 3))
    tv = ET.Element("tv")
    total, page, pages = 0, 1, 1
    while page <= pages:
        q = (f"classification_id=18&device_identifier=web&locale=en&market_code=uk&per_page=50&page={page}"
             f"&epg_starts_at={now:%Y-%m-%dT%H:%M:%S.000Z}&epg_ends_at={end:%Y-%m-%dT%H:%M:%S.000Z}"
             f"&epg_duration_minutes=360").replace(":", "%3A")
        try:
            j = _get_json("https://gizmo.rakuten.tv/v3/live_channels?" + q)
        except Exception as e:
            print(f"   !! rakuten page {page}: {e}", flush=True)
            break
        pages = ((j.get("meta") or {}).get("pagination") or {}).get("total_pages") or 1
        for c in j.get("data") or []:
            cid = f"rakuten-{c['id']}"
            ch = ET.SubElement(tv, "channel", id=cid)
            ET.SubElement(ch, "display-name").text = c.get("title") or cid
            imgs = c.get("images") or {}
            if imgs.get("artwork_negative") or imgs.get("artwork"):
                ET.SubElement(ch, "icon", src=imgs.get("artwork_negative") or imgs.get("artwork"))
            for pr in c.get("live_programs") or []:
                try:
                    s = datetime.datetime.fromisoformat(pr["starts_at"]); e = datetime.datetime.fromisoformat(pr["ends_at"])
                except Exception:
                    continue
                p = ET.SubElement(tv, "programme", start=s.astimezone(datetime.timezone.utc).strftime("%Y%m%d%H%M%S +0000"),
                                  stop=e.astimezone(datetime.timezone.utc).strftime("%Y%m%d%H%M%S +0000"), channel=cid)
                ET.SubElement(p, "title").text = pr.get("title") or c.get("title")
                if pr.get("subtitle"):
                    ET.SubElement(p, "sub-title").text = pr["subtitle"]
                if pr.get("description"):
                    ET.SubElement(p, "desc").text = pr["description"]
                total += 1
        page += 1
    ET.ElementTree(tv).write(out_path, encoding="utf-8", xml_declaration=True)
    print(f"   Rakuten TV UK: {total} programmes", flush=True)
    return out_path

def tbn_show_description(url, cache):
    """Fallback: the short description from a TBN show's own page (fetched once per show)."""
    import html as htmllib
    if url not in cache:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"})
            with urllib.request.urlopen(req, timeout=30) as r:
                page = r.read().decode("utf-8", "replace")
            m = re.search(r'<meta property="og:description" content="([^"]*)"', page)
            cache[url] = htmllib.unescape(m.group(1)).strip() if m else ""
        except Exception:
            cache[url] = ""
    return cache[url]

def grab_tbn_uk(days, out_path):
    """TBN UK's own TV guide (tbn.uk/tv-guide/<date>/), one page per day."""
    import html as htmllib
    tv = ET.Element("tv")
    ET.SubElement(ET.SubElement(tv, "channel", id="tbn-uk"), "display-name").text = "TBN UK"
    today = datetime.datetime.now(datetime.timezone.utc).date()
    seen, total, show_cache = set(), 0, {}
    for d in range(-1, int(days)):
        day = today + datetime.timedelta(days=d)
        try:
            req = urllib.request.Request(f"https://tbn.uk/tv-guide/{day.isoformat()}/", headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"})
            with urllib.request.urlopen(req, timeout=40) as r:
                page = r.read().decode("utf-8", "replace")
        except Exception as e:
            print(f"   !! tbn {day}: {e}", flush=True)
            continue
        for m in re.finditer(r"data-start-time='(\d+)' data-end-time='(\d+)'(?: data-genres=\"([^\"]*)\")?(.*?)(?=data-start-time=|\Z)", page, re.S):
            start_ms, end_ms, genres, rest = int(m.group(1)), int(m.group(2)), m.group(3), m.group(4)
            if start_ms in seen:
                continue
            seen.add(start_ms)
            title = re.search(r'aria-label="([^"]+)"', rest)
            synopsis = re.search(r"data-synopsis>(.*?)</div>", rest, re.S)
            desc = htmllib.unescape(re.sub(r"<[^>]+>|\s+", " ", synopsis.group(1))).strip() if synopsis else ""
            link = re.search(r'href="(https://tbn\.uk/tv/[^"]+)"', rest)
            if not desc and link:
                desc = tbn_show_description(link.group(1), show_cache)
            img = re.search(r'<img[^>]+src="([^"]+)"', rest)
            start = datetime.datetime.fromtimestamp(start_ms / 1000, datetime.timezone.utc)
            stop = datetime.datetime.fromtimestamp(end_ms / 1000, datetime.timezone.utc)
            p = ET.SubElement(tv, "programme", start=start.strftime("%Y%m%d%H%M%S +0000"),
                              stop=stop.strftime("%Y%m%d%H%M%S +0000"), channel="tbn-uk")
            ET.SubElement(p, "title").text = htmllib.unescape(title.group(1)) if title else "TBN UK"
            if desc:
                ET.SubElement(p, "desc").text = desc
            if img:
                ET.SubElement(p, "icon", src=re.sub(r"-60x60(\.\w+)$", r"-300x300\1", img.group(1)))
            for g in (genres or "").split():
                ET.SubElement(p, "category").text = g.replace("-", " ").title()
            total += 1
    ET.ElementTree(tv).write(out_path, encoding="utf-8", xml_declaration=True)
    print(f"   TBN UK guide: {total} programmes", flush=True)
    return out_path

def grab_islam_channel(days, out_path):
    """Islam Channel's own TV guide (the service behind islamchannel.tv/tv-guide). Times are UK local time."""
    import json
    from zoneinfo import ZoneInfo
    uk = ZoneInfo("Europe/London")
    tv = ET.Element("tv")
    ET.SubElement(ET.SubElement(tv, "channel", id="islam-channel"), "display-name").text = "Islam Channel"
    today = datetime.datetime.now(uk).date()
    seen, total, items = set(), 0, []
    for d in range(-1, int(days)):
        day = today + datetime.timedelta(days=d)
        data = urllib.parse.urlencode({"channel_id": 4, "date": day.isoformat()}).encode()
        req = urllib.request.Request("https://epg.etechnologies.com.tr/v1/api/dailySchedules/day-guide", data=data, headers={
            "User-Agent": "Mozilla/5.0", "Accept": "application/json", "Origin": "https://islamchannel.tv",
            "Referer": "https://islamchannel.tv/", "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"})
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                j = json.load(r)
        except Exception as e:
            print(f"   !! islam channel {day}: {e}", flush=True)
            continue
        for it in j.get("epg_details") or []:
            try:
                hh, mm = (int(x) for x in it["start_time"].split(":"))
                start = datetime.datetime(day.year, day.month, day.day, hh, mm, tzinfo=uk)
                stop = start + datetime.timedelta(minutes=int(it.get("epg_program_duration") or 30))
            except Exception:
                continue
            if start in seen:
                continue
            seen.add(start)
            items.append([start, stop, (it.get("epg_tilte") or it.get("epg_title") or "Islam Channel").strip(), (it.get("epg_synopsis") or "").strip()])
    items.sort(key=lambda x: x[0])
    for k, (start, stop, title, desc) in enumerate(items):
        if k + 1 < len(items) and stop > items[k + 1][0]:
            stop = items[k + 1][0]        # their data sometimes overlaps the next programme; end it when the next one starts
        p = ET.SubElement(tv, "programme", start=start.astimezone(datetime.timezone.utc).strftime("%Y%m%d%H%M%S +0000"),
                          stop=stop.astimezone(datetime.timezone.utc).strftime("%Y%m%d%H%M%S +0000"), channel="islam-channel")
        ET.SubElement(p, "title").text = title
        if desc:
            ET.SubElement(p, "desc").text = desc
        total += 1
    ET.ElementTree(tv).write(out_path, encoding="utf-8", xml_declaration=True)
    print(f"   Islam Channel guide: {total} programmes", flush=True)
    return out_path

def grab_bbc_ess(services, out_path):
    """BBC World Service TV schedules (BBC Arabic, Persian, Afghan/Pashto) from the BBC's own schedule service."""
    import json
    tv = ET.Element("tv")
    total = 0
    for sid in services:
        ET.SubElement(ET.SubElement(tv, "channel", id=f"ess-{sid}"), "display-name").text = sid
        try:
            req = urllib.request.Request(f"https://ess.api.bbci.co.uk/schedules?serviceId={sid}",
                                         headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=40) as r:
                items = json.load(r).get("items") or []
        except Exception as e:
            print(f"   !! bbc schedule {sid}: {e}", flush=True)
            continue
        for it in items:
            t = it.get("published_time") or {}
            if not t.get("start") or not t.get("end"):
                continue
            p = ET.SubElement(tv, "programme", start=_xmltv_time(t["start"]), stop=_xmltv_time(t["end"]), channel=f"ess-{sid}")
            brand = ((it.get("brand") or {}).get("title") or "").strip()
            ep = ((it.get("episode") or {}).get("title") or "").strip()
            ET.SubElement(p, "title").text = brand or ep or sid
            # the BBC often uses the first-broadcast date as the episode name ("04/11/2026 18:00 GMT") - leave those out
            is_date = bool(re.fullmatch(r"[\d/.:\-\s]+(GMT|BST|UTC)?", ep or ""))
            if brand and ep and ep != brand and not is_date:
                ET.SubElement(p, "sub-title").text = ep
            if not brand and is_date:
                p.find("title").text = sid
            total += 1
    ET.ElementTree(tv).write(out_path, encoding="utf-8", xml_declaration=True)
    print(f"   BBC World Service TV schedules: {total} programmes", flush=True)
    return out_path

def static_guide(path, days, out_path):
    """All-day listings for stations that publish no schedule (non-stop music streams).
    Reads lines of 'channel-id | title | description' and writes one listing per day."""
    tv = ET.Element("tv")
    today = datetime.datetime.now(datetime.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    n = 0
    for line in read_list(path):
        parts = [x.strip() for x in line.split("|")]
        if len(parts) < 2:
            continue
        cid, title, desc = parts[0], parts[1], (parts[2] if len(parts) > 2 else "")
        ET.SubElement(ET.SubElement(tv, "channel", id=cid), "display-name").text = title
        for d in range(-1, int(days)):
            start = today + datetime.timedelta(days=d)
            p = ET.SubElement(tv, "programme", start=start.strftime("%Y%m%d%H%M%S +0000"),
                              stop=(start + datetime.timedelta(days=1)).strftime("%Y%m%d%H%M%S +0000"), channel=cid)
            ET.SubElement(p, "title").text = title
            if desc:
                ET.SubElement(p, "desc").text = desc
            n += 1
    ET.ElementTree(tv).write(out_path, encoding="utf-8", xml_declaration=True)
    print(f"   Static guide: {n} all-day listings", flush=True)
    return out_path

# ---------------------------------------------------------------- Scottish football fixtures
ESPN = "https://site.api.espn.com/apis/site/v2/sports/soccer"
FOOTBALL_HOURS = 2         # how long each match listing lasts in the guide
FOOTBALL_RESULT_HOURS = 12 # how long the final score stays up after a match

def _plain(s):
    """Lower case, no accents, no 'FC', no punctuation: 'St. Mirren F.C.' -> 'st mirren'."""
    import unicodedata
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower().replace("&", " and ")
    s = re.sub(r"\b(a\.?f\.?c|f\.?c)\b\.?", " ", s)
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s).split())

def _uk_time(d):
    try:
        from zoneinfo import ZoneInfo
        d = d.astimezone(ZoneInfo("Europe/London"))
    except Exception:
        pass
    h = d.strftime("%I").lstrip("0") + (d.strftime(":%M") if d.minute else "") + d.strftime("%p").lower()
    return d.strftime("%a ") + str(d.day) + d.strftime(" %b, ") + h

def _team_names(t):
    return {_plain(t.get(k)) for k in ("displayName", "shortDisplayName", "name", "location") if t.get(k)}

def _score(c):
    sc = c.get("score")
    if isinstance(sc, dict):
        sc = sc.get("displayValue", sc.get("value"))
    try:
        return int(float(sc))
    except (TypeError, ValueError):
        return None

def read_football_config(config):
    lists, teams = ["sco.1", "sco.2", "sco.3", "sco.4", "uefa.nations"], []
    for line in read_list(config):
        if line.lower().startswith("team_lists") and "=" in line:
            lists = [x.strip() for x in line.split("=", 1)[1].split(",") if x.strip()]
        elif "|" in line:
            parts = [x.strip() for x in line.split("|")] + [""]
            names = {_plain(parts[1])} | {_plain(x) for x in parts[2].split(",") if x.strip()}
            teams.append({"id": parts[0], "name": parts[1], "names": names - {""}, "espn": None, "logo": None, "matches": {}})
    return lists, teams

def grab_scottish_football(config, days, out_path):
    """A guide channel for each team in football.txt: 'Next: ...' before a match, the match while it's on, then the final score."""
    lists, teams = read_football_config(config)
    # 1. Find each team's ESPN id and crest from the league team lists
    for lg in lists:
        if all(t["espn"] for t in teams):
            break
        try:
            data = _get_json(f"{ESPN}/{lg}/teams")
            found = [x["team"] for x in data["sports"][0]["leagues"][0]["teams"]]
        except Exception as e:
            print(f"   !! team list {lg}: {e}", flush=True)
            continue
        for t in teams:
            for et in found:
                if not t["espn"] and t["names"] & _team_names(et):
                    t["espn"] = et["id"]
                    t["logo"] = (et.get("logos") or [{}])[0].get("href") or et.get("logo")
    # 2. Each team's results and upcoming fixtures, in every competition
    now = datetime.datetime.now(datetime.timezone.utc)
    day0 = now.replace(hour=0, minute=0, second=0, microsecond=0) - datetime.timedelta(days=1)
    for t in teams:
        if not t["espn"]:
            print(f"   !! {t['name']}: not found in ESPN's team lists ({', '.join(lists)})", flush=True)
            continue
        for q in ("", "?fixture=true"):
            try:
                data = _get_json(f"{ESPN}/all/teams/{t['espn']}/schedule{q}")
            except Exception as e:
                print(f"   !! {t['name']} schedule{q}: {e}", flush=True)
                continue
            for ev in data.get("events") or []:
                try:
                    kickoff = datetime.datetime.fromisoformat(ev["date"].replace("Z", "+00:00"))
                    comp = (ev.get("competitions") or [{}])[0]
                    sides = comp.get("competitors") or []
                    home = next(c for c in sides if c.get("homeAway") == "home")
                    away = next(c for c in sides if c.get("homeAway") == "away")
                except Exception:
                    continue
                if kickoff < day0 - datetime.timedelta(hours=FOOTBALL_RESULT_HOURS):
                    continue
                us_home = str((home.get("team") or {}).get("id")) == str(t["espn"])
                notes = comp.get("notes") or []
                t["matches"][str(ev.get("id") or ev["date"])] = {
                    "kickoff": kickoff, "home": home, "away": away, "us_home": us_home,
                    "competition": (ev.get("league") or {}).get("name") or (ev.get("season") or {}).get("displayName") or "",
                    "round": (notes[0] or {}).get("headline") if notes else None,
                    "venue": (comp.get("venue") or {}).get("fullName"),
                    "state": ((comp.get("status") or {}).get("type") or {}).get("state")}

    def label(c):
        et = c.get("team") or {}
        for cfg in teams:
            if cfg["names"] & _team_names(et):
                return cfg["name"]
        return et.get("shortDisplayName") or et.get("displayName") or "TBC"

    def stamp(d):
        return d.astimezone(datetime.timezone.utc).strftime("%Y%m%d%H%M%S +0000")

    tv = ET.Element("tv")
    total = n_matches = 0
    horizon = day0 + datetime.timedelta(days=int(float(days)) + 2)
    logo_dir = os.path.join(HERE, "logos")
    for t in teams:
        ch = ET.SubElement(tv, "channel", id=t["id"])
        ET.SubElement(ch, "display-name").text = t["name"]
        path = os.path.join(logo_dir, t["id"] + ".png")
        repo = os.environ.get("GITHUB_REPOSITORY", "kem0sab3/my-epg")
        if os.path.exists(path):
            ET.SubElement(ch, "icon", src=f"https://raw.githubusercontent.com/{repo}/main/logos/{t['id']}.png")
        elif t["logo"]:
            ET.SubElement(ch, "icon", src=t["logo"])
            # until logos.txt fetches the Wikipedia crest, keep ESPN's crest so the playlist logo works
            if not os.path.exists(path):
                try:
                    req = urllib.request.Request(t["logo"], headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=30) as r:
                        data = r.read()
                    if data[:4] == b"\x89PNG":
                        os.makedirs(logo_dir, exist_ok=True)
                        with open(path, "wb") as f:
                            f.write(data)
                except Exception as e:
                    print(f"   !! crest for {t['name']}: {e}", flush=True)

        def add(start, stop, title, desc=None, icon=None):
            nonlocal total
            p = ET.SubElement(tv, "programme", start=stamp(start), stop=stamp(stop), channel=t["id"])
            ET.SubElement(p, "title").text = title
            if desc:
                ET.SubElement(p, "desc").text = desc
            ET.SubElement(p, "category").text = "Sports"
            if icon:
                ET.SubElement(p, "icon", src=icon)
            total += 1

        matches = sorted(t["matches"].values(), key=lambda m: m["kickoff"])
        n_matches += len(matches)
        cursor = day0
        for i, m in enumerate(matches + [None]):
            nxt = m["kickoff"] if m else horizon
            if cursor >= horizon:
                break
            if nxt > cursor + datetime.timedelta(minutes=30):
                if m:
                    them = m["away"] if m["us_home"] else m["home"]
                    add(cursor, min(nxt, horizon), f"Next: {label(them)} ({'H' if m['us_home'] else 'A'}) · {_uk_time(m['kickoff'])}",
                        f"{label(m['home'])} v {label(m['away'])}\n{m['competition']}" + (f" · {m['venue']}" if m["venue"] else ""))
                else:
                    add(cursor, horizon, f"{t['name']}: next fixture not announced yet")
            if not m:
                break
            ko, end = m["kickoff"], m["kickoff"] + datetime.timedelta(hours=FOOTBALL_HOURS)
            if end <= cursor:
                continue
            them = m["away"] if m["us_home"] else m["home"]
            crest = (them.get("team") or {}).get("logo") or ((them.get("team") or {}).get("logos") or [{}])[0].get("href")
            info = m["competition"] + (f" · {m['round']}" if m.get("round") else "") + (f" · {m['venue']}" if m["venue"] else "")
            hs, as_ = _score(m["home"]), _score(m["away"])
            if m["state"] == "post" and hs is not None and as_ is not None:
                result = f"{label(m['home'])} {hs}-{as_} {label(m['away'])}"
                add(ko, end, f"{result} (FT)", f"{info}\nKick-off {_uk_time(ko)}.", crest)
                later = matches[i + 1]["kickoff"] if i + 1 < len(matches) else horizon
                res_end = min(end + datetime.timedelta(hours=FOOTBALL_RESULT_HOURS), later)
                if res_end > end + datetime.timedelta(minutes=30):
                    add(end, res_end, f"FT: {result}", info, crest)
                    end = res_end
            else:
                add(ko, end, f"{label(m['home'])} v {label(m['away'])}", f"{info}\nKick-off {_uk_time(ko)}.", crest)
            cursor = end
    ET.ElementTree(tv).write(out_path, encoding="utf-8", xml_declaration=True)
    print(f"   Scottish football: {n_matches} matches, {total} listings for {len(teams)} teams", flush=True)
    return out_path

def update_football_only():
    """Refresh just the football listings inside epg.xml.gz (run every 15 minutes on match days, so scores appear soon after full time)."""
    src = next((s for s in read_list("sources.txt") if s.startswith("scottish-football:")), None)
    out_path = os.path.join(HERE, "epg.xml.gz")
    if not src or not os.path.exists(out_path):
        sys.exit("No scottish-football line in sources.txt, or no epg.xml.gz yet.")
    config = src.split(":", 1)[1].strip()
    ids = [t["id"] for t in read_football_config(config)[1]]
    tmp = tempfile.mkdtemp()
    new = open(grab_scottish_football(config, read_settings().get("days_ahead", 7), os.path.join(tmp, "f.xml")), encoding="utf-8").read()
    shutil.rmtree(tmp, ignore_errors=True)
    if "Next:" not in new and "FT" not in new:
        sys.exit("No fixtures came back - leaving the guide as it is.")
    alt = "|".join(re.escape(i) for i in ids)
    ch_re = re.compile(rf'<channel id="(?:{alt})">.*?</channel>\n?', re.S)
    pr_re = re.compile(rf'<programme [^>]*channel="(?:{alt})"[^>]*>.*?</programme>\n?', re.S)
    new_ch = "".join(m.group(0).rstrip("\n") + "\n" for m in ch_re.finditer(new))
    new_pr = "".join(m.group(0).rstrip("\n") + "\n" for m in pr_re.finditer(new))
    with gzip.open(out_path, "rt", encoding="utf-8") as f:
        text = f.read()
    old = "".join(m.group(0).rstrip("\n") + "\n" for m in ch_re.finditer(text)) + "".join(m.group(0).rstrip("\n") + "\n" for m in pr_re.finditer(text))
    if old == new_ch + new_pr:
        print("Football listings unchanged.")
        return
    text = pr_re.sub("", ch_re.sub("", text))
    first = text.find("<programme")
    text = (text[:first] + new_ch + text[first:]) if first >= 0 else text.replace("</tv>", new_ch + "</tv>")
    text = text.replace("</tv>", new_pr + "</tv>")
    with open(out_path + ".tmp", "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=9, mtime=0) as g:
        g.write(text.encode("utf-8"))
    os.replace(out_path + ".tmp", out_path)
    print("Football listings updated in epg.xml.gz")

def fetch(src, tmpdir, i, days=7):
    """Download (or copy) a source and return a path to the plain XML."""
    if src.startswith("scottish-football:"):
        return grab_scottish_football(src.split(":", 1)[1].strip(), days, os.path.join(tmpdir, f"src{i}.xml"))
    if src.startswith("bbc-ess:"):
        services = [x.strip() for x in src.split(":", 1)[1].split(",") if x.strip()]
        return grab_bbc_ess(services, os.path.join(tmpdir, f"src{i}.xml"))
    if src.strip() == "islam-channel":
        return grab_islam_channel(days, os.path.join(tmpdir, f"src{i}.xml"))
    if src.strip() == "tbn-uk":
        return grab_tbn_uk(days, os.path.join(tmpdir, f"src{i}.xml"))
    if src.startswith("static:"):
        return static_guide(src.split(":", 1)[1].strip(), days, os.path.join(tmpdir, f"src{i}.xml"))
    if src.startswith("bbc-radio:"):
        stations = [s.strip() for s in src.split(":", 1)[1].split(",") if s.strip()]
        return grab_bbc_radio(stations, int(days), os.path.join(tmpdir, f"src{i}.xml"))
    if src.startswith("bauer:"):
        stations = [s.strip() for s in src.split(":", 1)[1].split(",") if s.strip()]
        return grab_bauer(stations, int(days), os.path.join(tmpdir, f"src{i}.xml"))
    if src.startswith("sky:"):
        services = [s.strip() for s in src.split(":", 1)[1].split(",") if s.strip()]
        return grab_sky(services, int(days), os.path.join(tmpdir, f"src{i}.xml"))
    if src.strip() == "rakuten-uk":
        return grab_rakuten_uk(days, os.path.join(tmpdir, f"src{i}.xml"))
    raw = os.path.join(tmpdir, f"src{i}.raw")
    if os.path.exists(src):
        shutil.copy(src, raw)
    else:
        req = urllib.request.Request(src, headers={"User-Agent": "my-epg-builder/1.0"})
        with urllib.request.urlopen(req, timeout=300) as r, open(raw, "wb") as f:
            shutil.copyfileobj(r, f)
    with open(raw, "rb") as f:
        is_gz = f.read(2) == b"\x1f\x8b"
    if not is_gz:
        return raw
    plain = os.path.join(tmpdir, f"src{i}.xml")
    with gzip.open(raw, "rb") as g, open(plain, "wb") as f:
        shutil.copyfileobj(g, f)
    os.remove(raw)
    return plain

def refresh_plex_token():
    """Plex's free channels need a guest token (the same kind Plex's own web player uses when you're not signed in).
    Get a fresh one each run and put it into playlist.m3u, so the Plex links never go stale or get rate-limited."""
    import json, re, uuid
    path = os.path.join(HERE, "playlist.m3u")
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        text = f.read()
    if "epg.provider.plex.tv" not in text:
        return
    hdr = {"X-Plex-Product": "Plex Web", "X-Plex-Client-Identifier": str(uuid.uuid4()), "X-Plex-Version": "4.145.0",
           "X-Plex-Platform": "Chrome", "Accept": "application/json", "User-Agent": "Mozilla/5.0"}
    try:
        req = urllib.request.Request("https://plex.tv/api/v2/users/anonymous", data=b"", headers=hdr, method="POST")
        with urllib.request.urlopen(req, timeout=30) as r:
            token = json.load(r)["authToken"]
    except Exception as e:
        print(f"   !! could not get a Plex guest token, keeping the old one: {e}", flush=True)
        return
    text = re.sub(r"(epg\.provider\.plex\.tv/library/parts/[^?\s]+\?X-Plex-Token=)[^&\s]+", r"\g<1>" + token, text)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print("   Plex guest token refreshed", flush=True)

STREAMING_SERVICES = ("jmp2.uk/", "epg.provider.plex.tv/", "rakuten", "amagi.tv", "wurl.", "tubi.video")

def build_playlist(listed):
    """Make playlist.m3u from playlist_source.m3u. Channels from free streaming services (Pluto, Samsung, Rakuten, Plex)
    whose guide has nothing for them today are left out for today, and come back automatically when their listings return."""
    src = os.path.join(HERE, "playlist_source.m3u")
    if not os.path.exists(src):
        return
    with open(src, encoding="utf-8") as f:
        lines = f.read().splitlines()
    out, hidden, i = [], [], 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("#EXTINF"):
            block = [line]; j = i + 1
            while j < len(lines) and lines[j].startswith("#") and not lines[j].startswith("#EXTINF"):
                block.append(lines[j]); j += 1
            if j < len(lines):
                block.append(lines[j]); j += 1
            m = re.search(r'tvg-id="([^"]*)"', line)
            cid = m.group(1) if m else ""
            url = block[-1]
            if any(s in url for s in STREAMING_SERVICES) and cid not in listed:
                hidden.append(line.rsplit(",", 1)[-1])
            else:
                out.extend(block)
            i = j
        else:
            out.append(line); i += 1
    with open(os.path.join(HERE, "playlist.m3u"), "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print(f"   playlist.m3u: {sum(1 for l in out if l.startswith('#EXTINF'))} channels"
          f" ({len(hidden)} streaming channels hidden today for having no listings: {', '.join(hidden[:15])}{'...' if len(hidden) > 15 else ''})", flush=True)

def update_playlist_header():
    """Point playlist.m3u's first line at this repo's own epg.xml.gz, so apps load the guide automatically."""
    repo, branch = os.environ.get("GITHUB_REPOSITORY"), os.environ.get("GITHUB_REF_NAME") or "main"
    path = os.path.join(HERE, "playlist.m3u")
    if not repo or not os.path.exists(path):
        return
    link = f"https://raw.githubusercontent.com/{repo}/{branch}/epg.xml.gz"
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    header = f'#EXTM3U url-tvg="{link}" x-tvg-url="{link}"'
    if lines and lines[0].startswith("#EXTM3U"):
        lines[0] = header
    else:
        lines.insert(0, header)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"playlist.m3u now points to {link}")

def main():
    settings = read_settings()
    sources = read_list("sources.txt")
    wanted = set(read_list("channels.txt"))
    if not sources:
        sys.exit("sources.txt has no links in it.")
    now = datetime.datetime.now(datetime.timezone.utc)
    horizon = now + datetime.timedelta(days=float(settings.get("days_ahead", 7)))

    tmpdir = tempfile.mkdtemp()
    ch_out = open(os.path.join(tmpdir, "channels.part"), "w", encoding="utf-8")
    pr_out = open(os.path.join(tmpdir, "programmes.part"), "w", encoding="utf-8")
    channels_done = set()   # channel IDs already written
    owned = {}              # channel ID -> source number that supplies its listings
    listed = set()          # channel IDs that got at least one listing
    total_prog = 0
    ok_sources = 0

    for i, src in enumerate(sources):
        print(f"[{i+1}/{len(sources)}] {src}", flush=True)
        try:
            path = fetch(src, tmpdir, i, settings.get("days_ahead", 7))
        except Exception as e:
            print(f"   !! could not download, skipping: {e}", flush=True)
            continue
        n_ch = n_pr = 0
        seen = set()
        try:
            for _, el in ET.iterparse(path, events=("end",)):
                if el.tag == "channel":
                    cid = el.get("id")
                    if cid and cid not in channels_done and (not wanted or cid in wanted):
                        names = set()
                        for dn in list(el.findall("display-name")):
                            key = (dn.text or "").strip()
                            if key in names:
                                el.remove(dn)
                            names.add(key)
                        el.tail = "\n"
                        ch_out.write(ET.tostring(el, encoding="unicode"))
                        channels_done.add(cid)
                        n_ch += 1
                    el.clear()
                elif el.tag == "programme":
                    cid = el.get("channel")
                    if (not wanted or cid in wanted) and owned.setdefault(cid, i) == i:
                        start, stop = parse_time(el.get("start")), parse_time(el.get("stop"))
                        key = (cid, el.get("start"))
                        if not (stop and stop < now) and not (start and start > horizon) and key not in seen:
                            seen.add(key)
                            el.tail = "\n"
                            pr_out.write(ET.tostring(el, encoding="unicode"))
                            listed.add(cid)
                            n_pr += 1
                    el.clear()
            ok_sources += 1
        except ET.ParseError as e:
            print(f"   !! file is broken, kept what was read before the error: {e}", flush=True)
            ok_sources += 1
        os.remove(path)
        total_prog += n_pr
        print(f"   added {n_ch} channels, {n_pr} programmes", flush=True)

    ch_out.close(); pr_out.close()
    if ok_sources == 0 or total_prog == 0:
        sys.exit("Nothing could be downloaded - keeping the previous epg.xml.gz unchanged.")

    out_path = os.path.join(HERE, "epg.xml.gz")
    with gzip.open(out_path + ".tmp", "wt", encoding="utf-8", compresslevel=9) as out:
        name = settings["name"].replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")
        out.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        out.write(f'<tv generator-info-name="{name}">\n')
        for part in ("channels.part", "programmes.part"):
            with open(os.path.join(tmpdir, part), encoding="utf-8") as f:
                shutil.copyfileobj(f, out)
        out.write("</tv>\n")
    os.replace(out_path + ".tmp", out_path)
    shutil.rmtree(tmpdir, ignore_errors=True)
    build_playlist(listed)
    try:
        import refresh_links
        refresh_links.refresh()
    except Exception as e:
        print(f"   !! could not refresh radio links: {e}", flush=True)
    update_playlist_header()
    refresh_plex_token()
    mb = os.path.getsize(out_path) / 1e6
    print(f"Done: {len(channels_done)} channels, {total_prog} programmes, {mb:.1f} MB -> epg.xml.gz")

if __name__ == "__main__":
    if sys.argv[1:] == ["football"]:
        update_football_only()
    else:
        main()
