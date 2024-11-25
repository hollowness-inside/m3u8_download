import re
import asyncio
import argparse
from os import path, makedirs

from aiohttp import ClientSession

from m3u8_downloader import (
    download_m3u8,
    download_segment,
    combine_segments,
    load_headers,
    vprint as _vprint
)


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
    # Configure verbose printing
    global vprint
    vprint = print if args.verbose else lambda *_: None
    
    # Create segments directory
    makedirs(args.segments_dir, exist_ok=True)

    headers = load_headers(args.headers)

    async with ClientSession() as session:
        session.headers.update(headers)

        segments = await download_m3u8(
            session, 
            args.url,
            args.segments_cache,
            force_url_prefix=args.force_url_prefix,
            force_ext=args.force_ext
        )

        tasks = [download_segment(session, segment, args.segments_dir)
                for segment in segments]
        results = await asyncio.gather(*tasks)

        if all([i[0] for i in results]):
            print("All segments downloaded successfully!")
        else:
            print("Failed to download some segments")

        if not args.force_combine and not all([i[0] for i in results]):
            return

        results.sort(key=lambda x: int(
            re.search(r'(\d+)', path.split(x[1])[-1]).group()))

        with open(args.filelist, 'w') as f:
            for [success, fname] in results:
                if success:
                    f.write(f"file {fname}\n")

        combine_segments(args.filelist, args.output, remove_filelist=False)


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(args))
