from os import path
from .utils import vprint


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
            index += 1

            segments.append({
                "filename": key,
                "url": f"{prefix}{url}"
            })

    return segments
