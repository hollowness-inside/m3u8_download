# m3u8_download

Downloads segments from .m3u8 files and combines into a single video using ffmpeg.

I'm planning to write a CLI for this but am too lazy right now.

- **Extremely Fast** by utilizing the [asyncio](https://docs.python.org/3/library/asyncio.html) library.
- **Somewhat customizable** - you can enforce segment extensions and enforce a url prefix if m3u8 contains relative urls.

## Installation
- Install [aiohttp](https://pypi.org/project/aiohttp/)
> pip install aiohttp

## Usage

Check out the end of the `main.py`.
There you will find all the required configurations.

```python
# Prints all the logs
VERBOSE = False

if VERBOSE:
    vprint = lambda *args: print(*args)
else:
    vprint = lambda *_: None

# Path where parsed .m3u8 will be saved.
# Change to None if you don't want to cache.
# SEGMENTS_CACHE = "segments.pickle"
SEGMENTS_CACHE = None

# Path where segments will be downloaded
SEGMENTS_DIR = "segments"

# Path where filelist will be saved (required for ffmpeg)
FILELIST_PATH = "filelist.txt"

# Path where output video will be saved
OUTPUT_FILE = "output.mp4"

# Combine segments even if some failed to download
FORCE_COMBINE = True

# Some extra headers if the server is complaining about who you are
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36"
}

# A hint for parsing such headers is by going to Developers Console and
# grabbing any request and copying it as CURL (bash).
# Then go to https://curlconverter.com/ and convert it to python.
# Then just copy-paste the headers here.

# ----------------------------------------------

# The url to the m3u8 file
url = "some_url.m3u8"

# ----------------------------------------------

# Some m3u8's don't have any extension per segment
# Here, you can enforce it.

# Change to None to use automatic detection.
# ("automatic" is a big word here -- it just copies 
# everything after the last dot in the segment's url)
force_ext = ".ts"

# ----------------------------------------------

# Some m3u8's provide relative urls to the segments (i.e. /segment1.ts)
# Here, you can enforce the prefix
force_url_prefix = ""

asyncio.run(
    main(
        url=url,
        force_ext=force_ext,
        force_url_prefix=force_url_prefix)
)
```