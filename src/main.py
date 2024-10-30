import asyncio
from os import path


import aiohttp


VERBOSE = True

if VERBOSE:
    vprint = lambda *args: print(*args)
else:
    vprint = lambda *_: None


async def download_m3u8(session: aiohttp.ClientSession, url, force_ext: str | None = None):
    vprint("Downloading .m3u8")

    try:
        async with session.get(url) as response:
            response.raise_for_status()

            extension = force_ext
            segments = []
            index = 1

            text = await response.text()
            for url in text.splitlines():
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
    except:
        raise Exception("Failed to parse .m3u8")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36"
}


async def main():
    async with aiohttp.ClientSession() as session:
        session.headers.update(HEADERS)
        
        url = 'some_url.m3u8'
        segments = await download_m3u8(session, url, force_ext='.ts')
        print(segments)

asyncio.run(main())
