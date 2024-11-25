# m3u8_download

Downloads segments from .m3u8 files and combines them into a single video using ffmpeg.

## Features

- **Extremely Fast**: Utilizes [asyncio](https://docs.python.org/3/library/asyncio.html) and concurrent downloads
- **Configurable**: Control concurrent downloads, segment extensions, URL prefixes, and more
- **Caching**: Optional caching of parsed m3u8 files for faster subsequent runs
- **Flexible**: Supports both relative and absolute URLs in m3u8 files
- **Robust**: Handles failed downloads gracefully with options to force combine or skip

## Quick Start

1. Install dependencies:
```bash
pip install aiohttp
```

2. Make sure ffmpeg is installed and available in your PATH (or specify custom path with --ffmpeg)

3. Basic usage - download and combine segments:
```bash
python main.py "https://example.com/video.m3u8" --combine output.mp4
```

## Usage Examples

### Download segments only:
```bash
python main.py "https://example.com/video.m3u8"
```

### Download and combine into MP4:
```bash
python main.py "https://example.com/video.m3u8" --combine output.mp4
```

### Download and force combine into MP4:
In case some segments fail to download, use --force-combine to combine the downloaded segments anyway:
```bash
python main.py "https://example.com/video.m3u8" --force-combine output.mp4
```

### Download with custom headers (e.g., for authentication):
```bash
python main.py "https://example.com/video.m3u8" --headers headers.json --combine output.mp4
```

### Fix missing segments in a directory:
```bash
python main.py "https://example.com/video.m3u8" --fix segments
```

### Force specific extension for segments:
```bash
python main.py "https://example.com/video.m3u8" --force-ext .ts --combine output.mp4
```

### Use custom ffmpeg path:
```bash
python main.py "https://example.com/video.m3u8" --ffmpeg /path/to/ffmpeg --combine output.mp4
```

### Limit concurrent downloads:
```bash
python main.py "https://example.com/video.m3u8" --concurrent 5 --combine output.mp4
```

## Command Line Options

```
Arguments:
  url                   URL to the m3u8 file

Optional arguments:
  --segments-dir DIR          Directory to store segments (default: segments)         
  --force-ext EXT             Force specific extension for segments (e.g., .ts)         
  --force-url-prefix PREFIX   Force URL prefix for segments                             
  --cache FILE                Path to cache parsed m3u8                                 
  --filelist FILE             Path for ffmpeg filelist (default: filelist.txt)        
  --combine OUTPUT            Combine segments into OUTPUT file after download          
  --force-combine OUTPUT      Combine segments even if some failed to download         
  --cleanup                   Remove segments directory after successful combination     
  --fix DIR                   Fix missing segments in the specified directory (default: segments)
  --verbose, -v               Enable verbose output                                    
  --headers FILE              Path to JSON file containing request headers              
  --limit N                   Limit the number of segments to download                  
  --concurrent N              Number of concurrent downloads (default: 10)             
  --ffmpeg PATH               Path to ffmpeg executable (default: uses ffmpeg from system PATH)
```

## Headers File Format

The headers file should be a JSON file containing key-value pairs of HTTP headers:

```json
{
    "User-Agent": "Mozilla/5.0 ...",
    "Authorization": "Bearer token123"
}
```

## Helpful Tips

### Getting Website Headers

The easiest way to get headers is to use a browser's "Inspect" feature and copy any request on the website as `Copy as cURL (bash)`. Then, go to `https://curlconverter.com/json/` and paste the cURL there. You will see the "headers" field in the resulting JSON.

### Getting Stream URLs

This Google Chrome extension, [The Stream Detector](https://chromewebstore.google.com/detail/the-stream-detector/iakkmkmhhckcmoiibcfjnooibphlobak), captures all stream URLs on a website.

## Requirements

- Python 3.6+
- aiohttp
- ffmpeg (in PATH or specified via --ffmpeg)

## License

This project is open source and available under the MIT License.