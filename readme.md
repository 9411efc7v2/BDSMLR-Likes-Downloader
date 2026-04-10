# BDSMLR Likes Downloader

A Python script to scrape and collect image URLs from your liked posts on [bdsmlr.com](https://bdsmlr.com), outputting them to a text file for use with a download utility like `gallery-dl`.



## Features

- Scrapes all liked image posts across paginated likes feed
- Captures both original posts and reblogs
- Deduplicates URLs against existing output file
- Automatic retry on page loading error
- Automatic re-authentication if session expires mid-run
- Post-run report showing number of total downloads, successful and failed image extractions, and skipped pages
- Optional direct download via gallery-dl integration
- Updated UI for better useability and aesthetics

<img width="2598" height="1389" alt="Screenshot 2026-04-09 005127" src="https://github.com/user-attachments/assets/f6a3c0e8-d8fa-4fdc-ae9d-b1df74717416" />
<img width="2598" height="1389" alt="Screenshot 2026-04-09 004922" src="https://github.com/user-attachments/assets/a153c603-dc53-467c-b1a0-3a1d8f0d5593" />
<img width="2598" height="1389" alt="Screenshot 2026-04-09 005127(1)" src="https://github.com/user-attachments/assets/4451c62b-a380-4727-ab6b-1ff9e18023bb" />



## Requirements

```
pip install requests lxml colorama gallery-dl
```



## Authentication

Two methods are supported:

### Cookie file (recommended)
Export your bdsmlr session cookies in Netscape format using a browser extension:
- **Chrome/Edge**: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
- **Firefox**: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)

Then pass the file with `-c`:
```
python bdsmlr_get_likes.py -c C:\Path\To\cookies.txt
```

### Username & Password
Set your credentials as the defaults in the script, or pass them as arguments:
```
python bdsmlr_get_likes.py -u your@email.com -p yourpassword
```



## Usage

_Shift + Right-Click_ in the folder containing **bdsmlr_get_likes.py** and click _Open Powershell window here_. Then Run:

```
python bdsmlr_get_likes.py [options]
```

### Options

| Argument | Default | Description |
||||
| `-u`, `--username` | *[set in script]* | bdsmlr account email |
| `-p`, `--password` | *[set in script]* | bdsmlr account password |
| `-c`, `--cookies-file` | `None` | Path to Netscape cookies.txt file |
| `-s`, `--start-page` | `1` | Page to start scraping from |
| `-e`, `--end-page` | `None` | Page to stop scraping at (inclusive) |
| `-o`, `--output` | `bdsmlr_likes.txt` | Output file for collected URLs |
| `--tag` | *[set in script]* | Custom label shown in log messages |

### Examples

Scrape all likes from the beginning:
```
python bdsmlr_get_likes.py -c cookies.txt
```

Scrape pages 10 through 50:
```
python bdsmlr_get_likes.py -c cookies.txt -s 10 -e 50
```

Scrape with a custom log tag and custom output file:
```
python bdsmlr_get_likes.py -c cookies.txt --tag myuser -o my_likes.txt
```



## Output

URLs are written one per line to the output file (default: `bdsmlr_likes.txt`):

```
https://ocdn012.bdsmlr.com/uploads/photos/2026/03/424632/bdsmlr-424632-abc123.jpg
https://ocdn012.bdsmlr.com/uploads/photos/2026/03/245966/bdsmlr-245966-def456.jpeg
...
```



## Downloading Images

### gallery-dl

Use the built-in prompt at the end of the script to launch gallery-dl automatically, or start the download manually with:

```
gallery-dl -i bdsmlr_likes.txt
```





## Notes

- **Disable infinite scrolling** on your bdsmlr archive/likes page before running, otherwise pagination will not work
- The script is safe to re-run — existing URLs in the output file are loaded on startup and skipped
- Cookie files expire — if authentication fails, re-export your cookies and try again
- bdsmlr is unstable and frequently returns 502 errors; the script will retry automatically
