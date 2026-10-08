"""Build-time only. Pin latest release by tag, verify asset checksum, record versions."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import urllib.request

ROOT = Path(__file__).resolve().parent / 'vendor'
ROOT.mkdir(exist_ok=True)

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'NamiDownloader-build/0.1'})
    with urllib.request.urlopen(req, timeout=120) as response:
        return response.read()

# An explicit tag can reproduce a prior build; otherwise resolve once and record it.
tag = os.environ.get('NAMI_YTDLP_TAG')
if not tag:
    tag = json.loads(fetch('https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest'))['tag_name']
if not all(c.isalnum() or c in '.-_' for c in tag):
    raise RuntimeError('Invalid release tag')
base = f'https://github.com/yt-dlp/yt-dlp/releases/download/{tag}/'
checksums = fetch(base + 'SHA2-256SUMS').decode()
expected = next(line.split()[0] for line in checksums.splitlines() if line.split()[-1].lstrip('*') == 'yt-dlp_macos')
data = fetch(base + 'yt-dlp_macos')
if hashlib.sha256(data).hexdigest() != expected:
    raise RuntimeError('yt-dlp SHA256 verification failed')
(ROOT / 'yt-dlp').write_bytes(data)
(ROOT / 'yt-dlp').chmod(0o755)
versions = {'yt-dlp_tag': tag, 'yt-dlp_sha256': expected}
for name in ('ffmpeg', 'ffprobe', 'deno'):
    source = shutil.which(name)
    if not source: raise RuntimeError(f'Missing build dependency: {name}')
    shutil.copy2(Path(source).resolve(), ROOT / name)
    versions[name] = subprocess.check_output([source, '--version' if name == 'deno' else '-version'], text=True).splitlines()[0]
versions['build_macos'] = subprocess.check_output(['sw_vers', '-productVersion'], text=True).strip()
(ROOT / 'build-info.json').write_text(json.dumps(versions, ensure_ascii=False, indent=2))
print(json.dumps(versions, ensure_ascii=False, indent=2))
