import pickle
from os import path
from typing import Any, Coroutine

from aiohttp import ClientSession

from .parser import parse_m3u8
from .utils import vprint


async def download_m3u8(
    session: ClientSession,
    url: str,
    segments_cache: str | None,
    force_url_prefix: str = "",
    force_ext: str | None = None,
) -> Coroutine[Any, Any, list[dict[str, str]]]:
    vprint("Downloading .m3u8")

    if segments_cache and path.exists("segments.m3u8"):
        vprint("Using cached .m3u8")
        with open(segments_cache, "rb") as f:
            return pickle.load(f)

    try:
        async with session.get(url) as response:
            response.raise_for_status()
            text = await response.text()

            segments = parse_m3u8(
                m3u8_data=text, force_url_prefix=force_url_prefix, force_ext=force_ext
            )

            if segments_cache:
                vprint("Caching .m3u8")
                with open(segments_cache, "wb") as f:
                    pickle.dump(segments, f)

            return segments
    except:
        raise Exception("Failed to parse .m3u8")


async def download_segment(
    session: ClientSession, segment: dict[str, str], segments_dir: str
) -> Coroutine[Any, Any, bool]:
    vprint(f"Downloading segment {segment['filename']}...")

    fname = segment["filename"]
    url = segment["url"]
    fout = path.join(segments_dir, fname).replace("\\", "/")

    try:
        async with session.get(url) as response:
            response.raise_for_status()

            content = await response.read()

            with open(fout, "wb") as f:
                f.write(content)

            return [True, fout]
    except Exception as e:
        print(f"Failed to download {fname} : {e}")

    return [False, fout]
