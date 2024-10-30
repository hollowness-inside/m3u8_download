import re
import asyncio
import pickle

from os import path, makedirs, system, remove
from typing import Any, Coroutine

from aiohttp import ClientSession


VERBOSE = True
SEGMENTS_CACHE = "parsed_segments.pickle"
SEGMENTS_DIR = "segments"
FILELIST_PATH = "filelist.txt"
OUTPUT_FILE = "output.mp4"
FORCE_COMBINE = True

if VERBOSE:
    vprint = lambda *args: print(*args)
else:
    vprint = lambda *_: None


async def download_m3u8(
    session: ClientSession,
    url: str,
    force_url_prefix: str = "",
    force_ext: str | None = None,
    cache: bool = False
) -> Coroutine[Any, Any, list[dict[str, str]]]:

    vprint("Downloading .m3u8")

    if cache and path.exists("segments.m3u8"):
        vprint("Using cached .m3u8")
        with open(SEGMENTS_CACHE, "rb") as f:
            return pickle.load(f)

    try:
        async with session.get(url) as response:
            response.raise_for_status()
            text = await response.text()

            segments = parse_m3u8(
                m3u8_data=text,
                force_url_prefix=force_url_prefix,
                force_ext=force_ext
            )

            if cache:
                vprint("Caching .m3u8")
                with open(SEGMENTS_CACHE, "wb") as f:
                    pickle.dump(segments, f)

            return segments
    except:
        raise Exception("Failed to parse .m3u8")


def parse_m3u8(m3u8_data: str, force_url_prefix: str = "", force_ext: str | None = None) -> list[dict[str, str]]:
    vprint("Parsing .m3u8")

    prefix = force_url_prefix
    extension = force_ext
    segments = []
    index = 1

    for url in m3u8_data.splitlines():
        if not url.startswith('#') and url:
            if not extension:
                extension = path.splitext(url)[1]

            key = f'{index}{extension}'
            print('!!!! KEY: ', key, extension)
            index += 1

            segments.append({
                "filename": key,
                "url": f"{prefix}{url}"
            })

    return segments


async def download_segment(session: ClientSession, segment: dict[str, str]) -> Coroutine[Any, Any, bool]:
    vprint(f"Downloading segment {segment['filename']}...")

    fname = segment['filename']
    url = segment['url']
    fout = path.join(SEGMENTS_DIR, fname).replace('\\', '/')

    try:
        async with session.get(url) as response:
            response.raise_for_status()

            content = await response.read()

            with open(fout, 'wb') as f:
                f.write(content)

            return [True, fout]
    except Exception as e:
        print(f"Failed to download {fname} : {e}")

    return [False, fout]


def combine(ffmpeg_path: str = "ffmpeg", remove_filelist: bool = True):
    vprint("Combining segments...")

    system(
        f"{ffmpeg_path} -f concat -safe 0 -i {FILELIST_PATH} -c copy {OUTPUT_FILE}")

    if remove_filelist:
        vprint(f"Removing {FILELIST_PATH}...")
        remove(FILELIST_PATH)

    vprint("Combining segments finished...")


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36"
}


async def main():
    makedirs(SEGMENTS_DIR, exist_ok=True)

    async with ClientSession() as session:
        session.headers.update(HEADERS)

        url = 'some_url.m3u8'
        segments = await download_m3u8(session, url, force_ext='.ts')

        tasks = [download_segment(session, segment)
                 for segment in segments[:2]]
        results = await asyncio.gather(*tasks)

        if all([i[0] for i in results]):
            print("All segments downloaded successfully!")
        else:
            print("Failed to download some segments")

        if not FORCE_COMBINE:
            return

        results.sort(key=lambda x: int(
            re.search(r'(\d+)', path.split(x[1])[-1]).group()))

        with open(FILELIST_PATH, 'w') as f:
            for [success, fname] in results:
                if success:
                    f.write(f"file {fname}\n")

        combine(remove_filelist=False)


asyncio.run(main())
