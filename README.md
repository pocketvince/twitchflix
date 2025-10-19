<img src="https://raw.githubusercontent.com/pocketvince/twitchflix/main/logo.png?raw=true" alt="Twitchflix" title="Twitchflix" width="40%">


Watch your Twitch subs like Netflix

## Description
A Netflix-style interface for your Twitch subscriptions, finally making it easy to browse and enjoy new content

## Setup
1. Create application via Twitch API: https://dev.twitch.tv/docs/api/

2. Create multiple text files:
- clientid.txt: from twitch api
- secret.txt: from twitch api
- login.txt: the logins Twitch accounts you want to see (one per line)
  
→ token.txt will be generated automatically

```shell
python3 twitchflix.py
```

The script will generate “videos.json,” which you can run with “web.php” to see the result.

In the “Config” section of the script, you can edit options.

```shell
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
```


## Extra
Too impatient to watch Twitch replays (not yet available on YouTube),

I found the interface really complicated, having to watch account by account without a direct view.

This script solves the problem.

![Alt text](https://raw.githubusercontent.com/pocketvince/twitchflix/main/demo.gif?raw=true "demo")

## Extra
Readme generator: https://www.makeareadme.com/
