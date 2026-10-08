# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[('vendor/yt-dlp', 'vendor'), ('vendor/ffmpeg', 'vendor'), ('vendor/ffprobe', 'vendor'), ('vendor/deno', 'vendor')],
    datas=[('assets/icon.png', 'assets'), ('THIRD_PARTY.md', '.'), ('vendor/build-info.json', '.')],
    hiddenimports=[],
    hookspath=['packaging/hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='NamiDownloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='arm64',
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/NamiDownloader.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NamiDownloader',
)
app = BUNDLE(
    coll,
    name='NamiDownloader.app',
    icon='assets/NamiDownloader.icns',
    bundle_identifier='local.nami.downloader',
    info_plist={'CFBundleDisplayName': '纳米素材下载器', 'CFBundleShortVersionString': '0.1.0', 'CFBundleVersion': '1', 'LSMinimumSystemVersion': '13.0', 'NSHighResolutionCapable': True},
)
