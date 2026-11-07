# My UK TV

My UK TV playlist and guide (EPG) for TiviMate. Free, official streams only,
with the guide rebuilt automatically every day.

## Links for TiviMate

| What | Link |
|---|---|
| Playlist | `https://raw.githubusercontent.com/Kem0sab3/my-epg/main/playlist.m3u` |
| TV guide (EPG) | `https://raw.githubusercontent.com/Kem0sab3/my-epg/main/epg.xml.gz` |

- **Playlist:** TiviMate → Settings → Playlists → Add playlist → Enter URL
- **Guide:** TiviMate → Settings → EPG → EPG sources → Add source

## What's in the playlist

- **BBC:** every BBC TV channel and all BBC One regions in 1080p, 24 Red Button
  event streams, BBC World News and the BBC's Arabic, Persian and Pashto
  channels, plus 720p backups
- **BBC Radio, UK Radio and Irish Radio:** BBC, Global, Bauer, talkSPORT, Times Radio, Virgin, RTÉ and more
- **Sport**
- **Scottish Football:** a channel for each Premiership team and Scotland. The guide shows
  each match (competition, ground, kick-off) and which TV channel has it live, from Sky's guide
  (Sky Sports, Premier Sports, TNT Sports, BBC Scotland, BBC ALBA). Between matches it shows
  "Next: ...". Selecting a team plays BBC Radio Scotland, home of Sportsound commentary.
- **TV by category:** News, Entertainment, Comedy, Drama, Movies, Crime, Reality,
  Documentaries, Nature, Sci-Fi & Paranormal, Food & Lifestyle, Kids, Music,
  Christmas, Shopping, Faith and International. These mix the UK channels with
  the free channels from Pluto TV, Samsung TV Plus, Rakuten TV and Plex, with
  duplicates removed.

## How it updates

`playlist_source.m3u` is the full channel list. Each day GitHub builds `playlist.m3u`
(the one TiviMate loads) from it, leaving out any Pluto TV, Samsung TV Plus,
Rakuten TV or Plex channel that has no guide listings that day. Those channels
come back on their own when their listings return.

Every morning at about 3am, GitHub runs `build_epg.py`. It downloads every guide
in `sources.txt`, keeps only the channels listed in `channels.txt`, and saves the
result as `epg.xml.gz`. It also runs a minute after you change any of the files
below. To update straight away, open the **Actions** tab → **Update EPG** →
**Run workflow**.

## Radio links

Bauer's radio streams (Clyde 1, Forth 1, KISS, Magic, Absolute, Greatest Hits Radio and the rest)
only play when their link carries a recent session number. A small job (**Refresh radio links**)
updates it every 2 hours, so set TiviMate to reload the playlist regularly (every few hours).

## Changing things

Open a file, click the ✏️ pencil, make the change, then **Commit changes**.

| To… | Edit | How |
|---|---|---|
| Add a guide source | `sources.txt` | Paste the link on a new line. Higher in the list wins when two sources cover the same channel. |
| Switch the old epg6 guide back on | `sources.txt` | Remove the `#` from the start of the epg6 line. |
| Add or remove a channel | `playlist_source.m3u` and `channels.txt` | Each channel is two lines in `playlist_source.m3u`: the `#EXTINF` line and the link under it. Its `tvg-id` also needs to be in `channels.txt` to get guide listings. |
| Keep every channel from every guide | `channels.txt` | Delete all the IDs (keep the lines starting with `#`). |
| Show more or fewer days | `settings.txt` | Change `days_ahead`. |
| Add or remove a football team | `football.txt`, `playlist_source.m3u` and `channels.txt` | Copy a team's line in each file and change the name and id. The crest is saved in `logos/` on the next run. |
| Change the all-day listing for a non-stop music station | `static_guide.txt` | Edit the title or description on that station's line. |
| Add a logo from Wikipedia | `logos.txt` | Add a line like `bbc-radio-orkney \| BBC Radio Orkney` (file name \| Wikipedia article). GitHub downloads it, turns it white and saves it in `logos/`. Then set the channel's `tvg-logo` in `playlist.m3u` to `https://raw.githubusercontent.com/kem0sab3/my-epg/main/logos/` followed by the file name and `.png`. |

## If something goes wrong

- **Red ❌ in Actions:** click it to see what failed. If a guide source is down,
  the others are still used. If they all fail, yesterday's guide stays in place.
- **A channel has no listings:** its `tvg-id` doesn't match any guide source, or
  it's missing from `channels.txt`.
- **Updates stopped:** GitHub can pause daily runs after 60 days with no activity.
  Open **Actions** and switch the workflow back on.

Live BBC channels need a TV licence and only play on a UK connection.
