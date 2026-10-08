#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
trap 'echo "构建失败。请保存上方错误信息；不要把不完整的 dist 发给同事。"' ERR
if [[ "$(uname -s)" != Darwin || "$(uname -m)" != arm64 ]]; then
  echo '请在 Apple 芯片 Mac 的原生终端构建（不要通过 Rosetta）。'; exit 1
fi
if ! command -v brew >/dev/null; then
  echo '仅打包者需要 Homebrew。请从 https://brew.sh 安装后重新运行。'; exit 1
fi
# Build-machine dependencies only; users of the resulting .app do not need brew.
brew install python@3.12 ffmpeg deno
PYTHON="$(brew --prefix python@3.12)/bin/python3.12"
"$PYTHON" -m venv .build-venv
.build-venv/bin/python -m pip install -r requirements-build.txt
.build-venv/bin/python prepare_vendor.py
.build-venv/bin/python -m unittest discover -s tests -v
.build-venv/bin/python -m PyInstaller --noconfirm --clean --windowed --onedir \
  --name NamiDownloader --osx-bundle-identifier local.nami.downloader \
  --target-architecture arm64 \
  --icon assets/NamiDownloader.icns \
  --additional-hooks-dir packaging/hooks \
  --add-data assets/icon.png:assets \
  --add-binary vendor/yt-dlp:vendor \
  --add-binary vendor/ffmpeg:vendor \
  --add-binary vendor/ffprobe:vendor \
  --add-binary vendor/deno:vendor \
  --add-data THIRD_PARTY.md:. \
  --add-data vendor/build-info.json:. app.py
# Verify bundled executables run with a minimal PATH (no Homebrew discovery).
for tool in yt-dlp ffmpeg ffprobe deno; do
  tool_path="dist/NamiDownloader.app/Contents/Frameworks/vendor/$tool"
  if [[ ! -x "$tool_path" ]]; then
    tool_path="dist/NamiDownloader.app/Contents/Resources/vendor/$tool"
  fi
  flag=--version
  if [[ "$tool" == ffmpeg || "$tool" == ffprobe ]]; then flag=-version; fi
  env PATH=/usr/bin:/bin "$tool_path" "$flag" >/dev/null
done
codesign --verify --deep --strict dist/NamiDownloader.app
.build-venv/bin/python audit_bundle.py dist/NamiDownloader.app
stage="$(mktemp -d "${TMPDIR:-/tmp}/nami-dmg.XXXXXX")"
trap 'rm -rf "$stage"' EXIT
ditto dist/NamiDownloader.app "$stage/NamiDownloader.app"
ln -s /Applications "$stage/Applications"
cp README_zh.md "$stage/使用与测试说明.md"
hdiutil create -volname 'NamiDownloader' -srcfolder "$stage" -ov -format UDZO dist/NamiDownloader-arm64.dmg
echo '完成：dist/NamiDownloader-arm64.dmg'
echo '这是本地测试包，尚未经过 Apple 公证。请先在另一台无开发环境的 Mac 验收。'
open dist
