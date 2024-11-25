import re
import asyncio
import argparse
import shutil
from os import path, makedirs

from aiohttp import ClientSession, TCPConnector

from m3u8_downloader.combiner import combine_segments
from m3u8_downloader.downloader import download_m3u8, download_batch
from m3u8_downloader.utils import Config, vprint, load_headers


def parse_args():
    parser = argparse.ArgumentParser(description="Download and combine M3U8 segments")
    parser.add_argument("url", help="URL to the m3u8 file")
    parser.add_argument(
        "--segments-dir",
        default="segments",
        help="Directory to store segments (default: segments)",
    )
    parser.add_argument(
        "--force-ext", help="Force specific extension for segments (e.g., .ts)"
    )
    parser.add_argument(
        "--force-url-prefix", default="", help="Force URL prefix for segments"
    )
    parser.add_argument(
        "--cache", help="Path to cache parsed m3u8 (not stored by default)"
    )
    parser.add_argument(
        "--filelist",
        default="filelist.txt",
        help="Path for ffmpeg filelist (default: filelist.txt)",
    )
    parser.add_argument(
        "--combine",
        metavar="OUTPUT",
        help="Combine segments into OUTPUT file after download",
    )
    parser.add_argument(
        "--force-combine",
        metavar="OUTPUT",
        help="Combine segments into OUTPUT file even if some failed to download",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Remove segments directory after successful combination",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )
    parser.add_argument(
        "--headers", metavar="FILE", help="Path to JSON file containing request headers"
    )
    parser.add_argument(
        "--limit", type=int, help="Limit the number of segments to download"
    )
    parser.add_argument(
        "--concurrent",
        type=int,
        default=10,
        help="Number of concurrent downloads (default: 10)",
    )
    parser.add_argument(
        "--ffmpeg",
        help="Path to ffmpeg executable (default: uses ffmpeg from system PATH)",
    )
    return parser.parse_args()


async def main(args: argparse.Namespace) -> None:
    # Configure verbose printing
    Config.set_verbose(args.verbose)

    # Create segments directory
    makedirs(args.segments_dir, exist_ok=True)

    headers = load_headers(args.headers)

    # Configure connection pooling and reuse
    connector = TCPConnector(
        limit=args.concurrent,  # Limit number of concurrent connections
        force_close=False,  # Enable connection reuse
        enable_cleanup_closed=True,  # Clean up closed connections
    )

    async with ClientSession(connector=connector, headers=headers) as session:
        segments = await download_m3u8(
            session,
            args.url,
            args.cache,
            force_url_prefix=args.force_url_prefix,
            force_ext=args.force_ext,
        )

        # Apply segment limit if specified
        if args.limit:
            vprint(f"Limiting download to first {args.limit} segments")
            segments = segments[: args.limit]

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(args.concurrent)
        results = await download_batch(session, segments, args.segments_dir, semaphore)

        successful_downloads = [i[0] for i in results]
        if all(successful_downloads):
            print("All segments downloaded successfully!")
        else:
            failed_count = len([x for x in successful_downloads if not x])
            total_count = len(segments)
            print(f"Failed to download {failed_count} out of {total_count} segments")

        # Stop here if no combination is requested (neither --combine nor --force-combine)
        # or if there are failures and force combine is not set
        output_file = args.force_combine or args.combine
        if not output_file or (
            not args.force_combine and not all(successful_downloads)
        ):
            return

        results.sort(
            key=lambda x: int(re.search(r"(\d+)", path.split(x[1])[-1]).group())
        )

        with open(args.filelist, "w") as f:
            for [success, fname] in results:
                if success:
                    f.write(f"file {fname}\n")

        try:
            combine_segments(args.filelist, output_file, ffmpeg_path=args.ffmpeg, remove_filelist=args.cleanup)
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
