#!/usr/bin/env python3
"""Builds epg.xml.gz from the links in sources.txt.
Run by GitHub every day (see .github/workflows/update-epg.yml).
You shouldn't need to edit this file - change sources.txt / channels.txt / settings.txt instead."""
import datetime, gzip, os, shutil, sys, tempfile, urllib.request
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

def fetch(src, tmpdir, i, days=7):
    """Download (or copy) a source and return a path to the plain XML."""
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
    update_playlist_header()
    refresh_plex_token()
    mb = os.path.getsize(out_path) / 1e6
    print(f"Done: {len(channels_done)} channels, {total_prog} programmes, {mb:.1f} MB -> epg.xml.gz")

if __name__ == "__main__":
    main()
