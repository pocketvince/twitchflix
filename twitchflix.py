#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, time, json, pathlib, urllib.request, urllib.parse, urllib.error, sys, datetime
from typing import Optional, List, Dict, Any

# ====== Config ======
CLIENT_ID_PATH     = pathlib.Path("clientid.txt")
CLIENT_SECRET_PATH = pathlib.Path("secret.txt")
TOKEN_PATH         = pathlib.Path("token.txt")
LOGINS_PATH        = pathlib.Path("login.txt")
OUTPUT_PATH        = pathlib.Path("videos.json")

DAYS_BACK          = 3
INCLUDE_HIGHLIGHTS = "NO"
MAX_TOKEN_AGE_DAYS = 59
VIDEO_THUMB_SIZE   = (1280, 720)
BOX_ART_SIZE       = (342, 513)
GENERIC_PLACEHOLDER = "https://static-cdn.jtvnw.net/ttv-static/404_preview-320x180.jpg"

# ====== Utils ======
def _file_age_days(p: pathlib.Path) -> float:
    return (time.time() - p.stat().st_mtime) / 86400.0

def _read_file_trim(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8").strip()

def _post(url: str, data: dict) -> dict:
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))

def _get(url: str, headers: dict) -> dict:
    req = urllib.request.Request(url)
    for k,v in headers.items(): req.add_header(k, v)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))

def _fix_template(url: str, w: int, h: int) -> str:
    if not url: return ""
    u = (url.replace("%{width}", str(w)).replace("%{height}", str(h))
             .replace("{width}", str(w)).replace("{height}", str(h)))
    sep = "&" if "?" in u else "?"
    return f"{u}{sep}t={int(time.time())}"

def _parse_iso_utc(s: str) -> datetime.datetime:
    return datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)

def _yes(s: str) -> bool:
    return (s or "").strip().upper() == "YES"

# ====== Auth ======
def get_access_token(client_id: str, client_secret: str) -> str:
    if TOKEN_PATH.exists() and _file_age_days(TOKEN_PATH) < MAX_TOKEN_AGE_DAYS:
        return _read_file_trim(TOKEN_PATH)
    payload = _post("https://id.twitch.tv/oauth2/token", {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
    })
    token = payload["access_token"]
    TOKEN_PATH.write_text(token + "\n", encoding="utf-8")
    return token

def helix_headers(client_id: str, token: str) -> dict:
    return {"Client-ID": client_id, "Authorization": "Bearer " + token}

# ====== API ======
def get_user_id(login: str, headers: dict) -> Optional[str]:
    data = _get("https://api.twitch.tv/helix/users?login=" + urllib.parse.quote(login), headers)
    return data["data"][0]["id"] if data.get("data") else None

# NEW: profil cache + fetch
_user_profile_cache: Dict[str, Dict[str, str]] = {}  # user_id -> {"profile_image_url":..., "display_name":...}

def get_user_profile(user_id: str, headers: dict) -> Dict[str, str]:
    """Retourne {'profile_image_url','display_name'}; cache en mémoire."""
    if user_id in _user_profile_cache:
        return _user_profile_cache[user_id]
    data = _get("https://api.twitch.tv/helix/users?id=" + urllib.parse.quote(user_id), headers)
    profile_image_url = ""
    display_name = ""
    if data.get("data"):
        u = data["data"][0]
        profile_image_url = u.get("profile_image_url", "") or ""
        display_name = u.get("display_name", "") or ""
    _user_profile_cache[user_id] = {"profile_image_url": profile_image_url, "display_name": display_name}
    return _user_profile_cache[user_id]

def fetch_videos_since(user_id: str, since_utc: datetime.datetime, headers: dict, hard_cap: int = 1000) -> List[Dict[str,Any]]:
    out, cursor, fetched = [], None, 0
    base = f"https://api.twitch.tv/helix/videos?user_id={urllib.parse.quote(user_id)}&first=100"
    while True:
        url = base + (f"&after={urllib.parse.quote(cursor)}" if cursor else "")
        data = _get(url, headers)
        items = data.get("data", [])
        if not items: break
        for v in items:
            fetched += 1
            created = _parse_iso_utc(v.get("created_at","1970-01-01T00:00:00Z"))
            if created >= since_utc:
                out.append(v)
            else:
                return out
            if fetched >= hard_cap: return out
        cursor = (data.get("pagination") or {}).get("cursor")
        if not cursor: break
    return out

# ====== Images ======
_game_box_cache: Dict[str,str] = {}          # game_id -> box_art_url template
_channel_game_cache: Dict[str, str] = {}     # user_id -> last/current game_id

def get_box_art_by_game(game_id: str, headers: dict) -> str:
    if not game_id: return ""
    if game_id in _game_box_cache:
        return _fix_template(_game_box_cache[game_id], BOX_ART_SIZE[0], BOX_ART_SIZE[1])
    data = _get("https://api.twitch.tv/helix/games?id=" + urllib.parse.quote(game_id), headers)
    if not data.get("data"): return ""
    tmpl = data["data"][0].get("box_art_url","")
    _game_box_cache[game_id] = tmpl
    return _fix_template(tmpl, BOX_ART_SIZE[0], BOX_ART_SIZE[1])

def get_channel_game_id(user_id: str, headers: dict) -> str:
    if user_id in _channel_game_cache:
        return _channel_game_cache[user_id]
    data = _get("https://api.twitch.tv/helix/channels?broadcaster_id=" + urllib.parse.quote(user_id), headers)
    game_id = data["data"][0].get("game_id","") if data.get("data") else ""
    _channel_game_cache[user_id] = game_id
    return game_id

def vod_thumbnail(url: str) -> str:
    return _fix_template(url or "", VIDEO_THUMB_SIZE[0], VIDEO_THUMB_SIZE[1])

def is_thumb_broken(url: str) -> bool:
    if not url: return True
    u = url.lower()
    return ("_404" in u) or ("404_processing" in u)

def pick_thumbnail(v: dict, user_id: str, headers: dict) -> str:
    t = vod_thumbnail(v.get("thumbnail_url",""))
    if not is_thumb_broken(t): return t
    game_id = v.get("game_id","") or ""
    img = get_box_art_by_game(game_id, headers) if game_id else ""
    if img: return img
    ch_game = get_channel_game_id(user_id, headers)
    img = get_box_art_by_game(ch_game, headers) if ch_game else ""
    if img: return img
    return GENERIC_PLACEHOLDER

# ====== Main ======
def main():
    if not CLIENT_ID_PATH.exists() or not CLIENT_SECRET_PATH.exists():
        sys.exit("clientid.txt or secret.txt are missing")
    client_id = _read_file_trim(CLIENT_ID_PATH)
    client_secret = _read_file_trim(CLIENT_SECRET_PATH)

    if not LOGINS_PATH.exists():
        sys.exit("file login.txt missing")
    logins = [ln.strip() for ln in LOGINS_PATH.read_text(encoding="utf-8").splitlines()
              if ln.strip() and not ln.strip().startswith("#")]
    if not logins:
        sys.exit("no login on login.txt.")

    since_utc = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=DAYS_BACK)

    token = get_access_token(client_id, client_secret)
    headers = helix_headers(client_id, token)
    include_highlights = _yes(INCLUDE_HIGHLIGHTS)

    out: List[Dict[str,Any]] = []

    for login in logins:
        try:
            uid = get_user_id(login, headers)
            if not uid:
                print(f"Channel not found: {login}")
                continue

            prof = get_user_profile(uid, headers)
            pp_url = prof.get("profile_image_url","")
            display_name = prof.get("display_name","") or login  # fallback

            vids = fetch_videos_since(uid, since_utc, headers)
            if not vids:
                print(f"No video found for the last {DAYS_BACK} day(s) for: {login}")
                continue

            for v in vids:
                vtype = (v.get("type") or "").lower()  # archive | highlight | upload
                if not include_highlights and vtype == "highlight":
                    continue
                thumb = pick_thumbnail(v, uid, headers)
                out.append({
                    "login": login,
                    "display_name": display_name,
                    "profile_image_url": pp_url,
                    "url": v.get("url",""),
                    "thumbnail_url": thumb,
                    "title": v.get("title",""),
                    "created_at": v.get("created_at",""),
                    "language": v.get("language",""),
                    "duration": v.get("duration",""),
                    "type": vtype
                })

        except urllib.error.HTTPError as e:
            print(f"http error for {login}: {e}")
        except Exception as e:
            print(f"error for {login}: {e}")

    OUTPUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Export → {OUTPUT_PATH.resolve()} ({len(out)} videos, {DAYS_BACK} days, highlights={'ON' if include_highlights else 'OFF'})")

if __name__ == "__main__":
    main()
