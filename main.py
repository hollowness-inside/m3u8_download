import re
import asyncio
import pickle
import argparse
import json

from os import path, makedirs, system, remove
from typing import Any, Coroutine

from aiohttp import ClientSession


async def download_m3u8(
    session: ClientSession,
    url: str,
    force_url_prefix: str = "",
    force_ext: str | None = None,
) -> Coroutine[Any, Any, list[dict[str, str]]]:
    global SEGMENTS_CACHE

    vprint("Downloading .m3u8")

    if SEGMENTS_CACHE and path.exists("segments.m3u8"):
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

            if SEGMENTS_CACHE:
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
    global SEGMENTS_DIR

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
    global FILELIST_PATH, OUTPUT_FILE

    vprint("Combining segments...")

    system(
        f"{ffmpeg_path} -f concat -safe 0 -i {FILELIST_PATH} -c copy {OUTPUT_FILE}")

    if remove_filelist:
        vprint(f"Removing {FILELIST_PATH}...")
        remove(FILELIST_PATH)

    vprint("Combining segments finished...")


def load_headers(header_file: str | None) -> dict:
    """Load headers from a JSON file or return default headers."""
    if header_file and path.exists(header_file):
        try:
            with open(header_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Failed to parse header file {header_file}. Using default headers.")
        except Exception as e:
            print(f"Warning: Error reading header file {header_file}: {e}. Using default headers.")
    
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36"
    }


def parse_args():
    parser = argparse.ArgumentParser(description='Download and combine M3U8 segments')
    parser.add_argument('url', help='URL to the m3u8 file')
    parser.add_argument('--output', '-o', default='output.mp4',
                      help='Output file path (default: output.mp4)')
    parser.add_argument('--segments-dir', default='segments',
                      help='Directory to store segments (default: segments)')
    parser.add_argument('--force-ext', 
                      help='Force specific extension for segments (e.g., .ts)')
    parser.add_argument('--force-url-prefix', default='',
                      help='Force URL prefix for segments')
    parser.add_argument('--segments-cache', 
                      help='Path to cache parsed m3u8 (disabled by default)')
    parser.add_argument('--filelist', default='filelist.txt',
                      help='Path for ffmpeg filelist (default: filelist.txt)')
    parser.add_argument('--force-combine', action='store_true',
                      help='Combine segments even if some failed to download')
    parser.add_argument('--verbose', '-v', action='store_true',
                      help='Enable verbose output')
    parser.add_argument('--headers',
                      help='Path to JSON file containing request headers')
    return parser.parse_args()


async def main(args: argparse.Namespace) -> None:
    global vprint, SEGMENTS_DIR, FILELIST_PATH, OUTPUT_FILE, SEGMENTS_CACHE, FORCE_COMBINE
    
    # Configure verbose printing
    vprint = print if args.verbose else lambda *_: None
    
    # Create segments directory
    SEGMENTS_DIR = args.segments_dir
    makedirs(SEGMENTS_DIR, exist_ok=True)

    FILELIST_PATH = args.filelist
    OUTPUT_FILE = args.output
    SEGMENTS_CACHE = args.segments_cache
    FORCE_COMBINE = args.force_combine

    headers = load_headers(args.headers)

    async with ClientSession() as session:
        session.headers.update(headers)

        segments = await download_m3u8(
            session, 
            args.url, 
            force_url_prefix=args.force_url_prefix,
            force_ext=args.force_ext
        )

        tasks = [download_segment(session, segment)
                for segment in segments]
        results = await asyncio.gather(*tasks)

        if all([i[0] for i in results]):
            print("All segments downloaded successfully!")
        else:
            print("Failed to download some segments")

        if not FORCE_COMBINE and not all([i[0] for i in results]):
            return

        results.sort(key=lambda x: int(
            re.search(r'(\d+)', path.split(x[1])[-1]).group()))

        with open(FILELIST_PATH, 'w') as f:
            for [success, fname] in results:
                if success:
                    f.write(f"file {fname}\n")

        combine(remove_filelist=False)

if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(args))
