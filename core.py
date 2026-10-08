"""Platform adapters and shell-free download arguments."""
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit
import re
import sys

@dataclass(frozen=True)
class Platform:
    name: str
    domains: tuple[str, ...]
    enabled: bool = True

# Add adapters here; unsupported platforms never silently fall through.
PLATFORMS = (
    Platform('YouTube', ('youtube.com', 'youtu.be')),
    Platform('B站', ('bilibili.com', 'b23.tv')),
    Platform('抖音', ('douyin.com',), False),
    Platform('TikTok', ('tiktok.com',), False),
    Platform('小红书', ('xiaohongshu.com', 'xhslink.com'), False),
)

def platform_for(url):
    parsed = urlsplit(url)
    if parsed.scheme not in ('https', 'http') or parsed.username or parsed.password:
        raise ValueError('请输入 http/https 视频链接')
    host = (parsed.hostname or '').lower()
    for platform in PLATFORMS:
        if any(host == d or host.endswith('.' + d) for d in platform.domains):
            if not platform.enabled:
                raise ValueError(f'{platform.name} 尚未接入，第一版仅支持 YouTube 和B站')
            return platform
    raise ValueError('暂不支持这个网站')

def extract_urls(text):
    return list(dict.fromkeys(u.rstrip('。，,；;！!）)]>') for u in re.findall(r'https?://[^\s<>"\u3000]+', text)))

def tools_dir():
    return Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent)) / 'vendor'

def command(url, output, number, quality, browser='', proxy=''):
    platform_for(url)
    root = tools_dir()
    ceiling = int(quality)
    args = [str(root / 'yt-dlp'), '--ignore-config', '--no-playlist', '--newline',
            '--no-colors', '--no-overwrites', '--continue', '--retries', '3',
            '--fragment-retries', '3', '--socket-timeout', '30',
            '--ffmpeg-location', str(root), '--js-runtimes', f'deno:{root / "deno"}',
            '--format', f'bv*[height<={ceiling}]+ba/b[height<={ceiling}]',
            '--merge-output-format', 'mp4', '--remux-video', 'mp4',
            '--progress', '--progress-template', 'download:NAMI_PROGRESS:%(progress._percent_str)s',
            '--print', 'after_move:NAMI_FILE:%(filepath)s',
            '--paths', str(output), '--output', f'{number:04d}_%(id)s.%(ext)s']
    if browser:
        args += ['--cookies-from-browser', browser]
    if proxy:
        parsed = urlsplit(proxy)
        if parsed.scheme not in ('http', 'https', 'socks5', 'socks5h') or not parsed.hostname:
            raise ValueError('代理格式应类似 http://127.0.0.1:7890')
        if parsed.username or parsed.password:
            raise ValueError('第一版代理暂不支持包含账号密码的地址')
        args += ['--proxy', proxy]
    return args + ['--', url]

def friendly_error(text):
    s = text.lower()
    if 'cookie' in s or 'sign in' in s or 'login' in s or '登录' in s:
        return '需要登录或读取登录状态失败：先在浏览器登录，再选择对应浏览器重试。'
    if '403' in s or '429' in s or '412' in s:
        return '平台拒绝请求或限流：稍后重试，必要时选择已登录的浏览器。'
    if any(x in s for x in ('timed out', 'resolve', 'connection', 'proxy')):
        return '网络连接失败：确认能访问视频，并检查代理设置。'
    if 'requested format' in s:
        return '没有符合所选清晰度的资源：尝试调整清晰度或登录后重试。'
    if 'unsupported url' in s:
        return '此链接类型暂不支持，请使用单个视频页面链接。'
    return '下载失败：可能是视频不可用或解析引擎需要更新。可在任务详情查看脱敏错误。'

def redact(text):
    text = re.sub(r'https?://\S+', '[链接已隐藏]', text)
    return re.sub(r'(?i)(cookie|authorization|token)\s*[:=].*', r'\1=[已隐藏]', text)
