import asyncio
import pickle
from os import path, makedirs

import aiohttp


VERBOSE = True
SEGMENTS_CACHE = "parsed_segments.pickle"
SEGMENTS_DIR = "segments"

makedirs(SEGMENTS_DIR, exist_ok=True)

if VERBOSE:
    vprint = lambda *args: print(*args)
else:
    vprint = lambda *_: None


async def download_m3u8(session: aiohttp.ClientSession, url: str, force_ext: str | None = None, cache: bool = False):
    vprint("Downloading .m3u8")

    if cache and path.exists("segments.m3u8"):
        vprint("Using cached .m3u8")
        with open(SEGMENTS_CACHE, "rb") as f:
            return pickle.load(f)

    try:
        async with session.get(url) as response:
            response.raise_for_status()
            text = await response.text()

            segments = parse_m3u8(text, force_ext)

            if cache:
                vprint("Caching .m3u8")
                with open(SEGMENTS_CACHE, "wb") as f:
                    pickle.dump(segments, f)

            return segments
    except:
        raise Exception("Failed to parse .m3u8")


def parse_m3u8(m3u8_data: str, force_ext: str | None = None):
    vprint("Parsing .m3u8")

    extension = force_ext
    segments = []
    index = 1

    for url in m3u8_data.splitlines():
        if not url.startswith('#') and url:
            if not extension:
                extension = path.splitext(url)[1]

            key = f'{index}{extension}'
            if key in segments:
                raise Exception(f"Duplicate segment {key} in .m3u8")
            index += 1

            segments.append({
                "filename": key,
                "url": url
            })

    return segments


async def download_segment(session: aiohttp.ClientSession, segment: dict[str, str]):
    fname = segment['filename']
    url = segment['url']

    try:
        async with session.get(url) as response:
            response.raise_for_status()

            content = await response.read()

            fout = path.join(SEGMENTS_DIR, fname)
            with open(fout, 'wb') as f:
                f.write(content)

            vprint(f"Downloaded segment {fname}")
    except Exception as e:
        vprint(f"Failed to download segment {fname}: {e}")


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36"
}


async def main():
    async with aiohttp.ClientSession() as session:
        session.headers.update(HEADERS)

        url = 'some_url.m3u8'
        segments = await download_m3u8(session, url, force_ext='.ts')
        print(segments)

        await download_segment(session, segments[0])

asyncio.run(main())
