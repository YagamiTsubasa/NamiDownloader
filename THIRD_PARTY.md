# Third-party components / 分发说明

本工程源码为纳米定制的测试原型。打包时会加入以下第三方组件：

- PySide6 / Qt: https://doc.qt.io/qtforpython-6/licenses.html
- PyInstaller: https://pyinstaller.org/en/stable/license.html
- Python: https://docs.python.org/3/license.html
- yt-dlp standalone: https://github.com/yt-dlp/yt-dlp （独立发行程序还包含第三方依赖；以选定发布版本说明为准）
- FFmpeg / ffprobe: https://ffmpeg.org/legal.html （许可证取决于 Homebrew 构建所启用的组件）
- Deno: https://github.com/denoland/deno/blob/main/LICENSE.md

此文件是组件索引，不是全部许可证文本，也不能代替对应源码提供义务。
当前交付只有原创工程源码，未附第三方二进制文件。正式分发构建产物前，应按实际构建版本收集许可证、版权声明及适用的对应源码/重新链接材料。
Homebrew FFmpeg 可引入大量库；如需精简正式发行版，应制作明确配置、可复现的 FFmpeg 构建并保留源码和构建参数。
