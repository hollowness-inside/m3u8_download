import re
import asyncio
import argparse
import shutil
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
    parser.add_argument('--combine', metavar='OUTPUT',
                      help='Combine segments into OUTPUT file after download')
    parser.add_argument('--force-combine', metavar='OUTPUT',
                      help='Combine segments into OUTPUT file even if some failed to download')
    parser.add_argument('--cleanup', action='store_true',
                      help='Remove segments directory after successful combination')
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

        successful_downloads = [i[0] for i in results]
        if all(successful_downloads):
            print("All segments downloaded successfully!")
        else:
            failed_count = len([x for x in successful_downloads if not x])
            print(f"Failed to download {failed_count} segments")

        # Stop here if no combination is requested (neither --combine nor --force-combine)
        # or if there are failures and force combine is not set
        output_file = args.force_combine or args.combine
        if not output_file or (not args.force_combine and not all(successful_downloads)):
            return

        results.sort(key=lambda x: int(
            re.search(r'(\d+)', path.split(x[1])[-1]).group()))

        with open(args.filelist, 'w') as f:
            for [success, fname] in results:
                if success:
                    f.write(f"file {fname}\n")

        try:
            combine_segments(args.filelist, output_file, remove_filelist=args.cleanup)
            if args.cleanup:
                # Only cleanup if combination was successful
                vprint(f"Cleaning up segments directory {args.segments_dir}...")
                shutil.rmtree(args.segments_dir)
        except Exception as e:
            print(f"Failed to combine segments: {e}")
            return


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(args))
