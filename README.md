# BookVoice Studio / 书声工坊

BookVoice Studio（书声工坊）是一款本地电子书转有声书工具，基于 `epub2mp3` 改造升级。它使用 Microsoft Edge TTS 将 EPUB/TXT/DOCX 电子书转换为 MP3 音频文件，并实验支持 MOBI/AZW3。

## 特性

- 支持多种微软 Edge TTS 语音选项
- 支持 EPUB、TXT、DOCX 输入，实验支持 MOBI/AZW3
- 并发处理章节，提高转换效率
- 智能限流和重试机制
- 可自定义的输出目录和文件命名
- 支持错误重试
- 支持为章节音频添加背景音乐
- 支持写入歌词
- 支持写入 MP3 章节元数据和封面
- 支持转换完成后生成整本 M4B
- 桌面界面支持暂停/继续/取消转换
- 桌面界面支持多本书批量队列

## 帮助

```
pdm start -h
usage: main.py [-h] [-v VOICE] [-o OUTPUT_DIR] [-r RETRIES] [-b BG_DIR]
               [-c CONCURRENCY] [--no-high-quality] [--no-lyrics]
               [--rate RATE] [--volume VOLUME] [--pitch PITCH]
               [--cover COVER_PATH] [--no-mp3-metadata] [--m4b]
               [--overwrite-existing] [--check-env]
               [epub_path]

将 EPUB/TXT/DOCX/MOBI/AZW3 电子书转换为 MP3 音频文件，每章一个文件。MOBI/AZW3 需要本机安装 Calibre ebook-convert，且不支持 DRM 加密文件。

positional arguments:
  epub_path             要转换的 EPUB/TXT/DOCX/MOBI/AZW3 文件的路径。

options:
  -h, --help            show this help message and exit
  -v VOICE, --voice VOICE
                        用于文本转语音的 Edge TTS 声音。
                        例如: zh-CN-YunxiNeural, en-US-AriaNeural
                        使用 'edge-tts --list-voices' 命令查看所有可用声音。
                        默认值: zh-CN-YunxiaNeural
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                        保存生成的 MP3 文件的目录。
                        默认值: output_audio
  -r RETRIES, --retries RETRIES
                        转换失败时的最大重试次数。
                        默认值: 3
  -b BG_DIR, --bg-dir BG_DIR
                        背景音乐文件所在目录，如果指定，程序会随机择一个背景音乐添加到每个章节的音频中。
                        默认不添加背景音乐。
  -c CONCURRENCY, --concurrency CONCURRENCY
                        同时转换的最大章节数。
                        默认值: 3
  --no-high-quality     跳过 320kbps/48kHz 高质量转码，加快转换速度。
  --no-lyrics           跳过歌词标签写入，加快转换速度。
  --rate RATE           语速，例如 -20%, +0%, +15%。默认值: +0%
  --volume VOLUME       音量，例如 -10%, +0%, +10%。默认值: +0%
  --pitch PITCH         音调，例如 -5Hz, +0Hz, +5Hz。默认值: +0Hz
  --cover COVER_PATH    封面图片路径，支持 JPG/JPEG/PNG，会写入章节 MP3 和 M4B。
  --no-mp3-metadata     跳过 MP3 章节标题、书名、作者和封面元数据写入。
  --m4b                 转换完成后生成整本 M4B 有声书文件。
  --overwrite-existing  覆盖已存在的章节 MP3，重新转换同名章节。
  --ebook-convert PATH   指定 Calibre ebook-convert.exe 路径。
  --check-env           检查 Python、依赖包和 ffmpeg 是否可用，然后退出。
```

环境检查：

```shell
pdm start --check-env
```

MOBI/AZW3 需要安装 Calibre，并确保 `ebook-convert` 可用。检测顺序是：GUI/CLI 指定路径、程序旁 `calibre/ebook-convert.exe`、系统 PATH、Windows 常见安装路径 `C:\Program Files\Calibre2\ebook-convert.exe`。DRM 加密电子书不支持。

## 桌面界面

源码运行版桌面界面：

```shell
pdm gui
```

Windows 下也可以直接双击项目根目录的 `start_gui.bat` 启动。

首次打开 GUI 会显示“书声工坊 首次使用指南”，之后可通过“使用说明”按钮再次查看。

界面支持选择 EPUB/TXT/DOCX/MOBI/AZW3 文件、预览章节、勾选要转换的章节、选择音色、语速、音量、音调、输出目录、背景音乐目录、封面图片、Calibre 路径、重试次数、并发章节数，并可以关闭高质量转码、歌词写入或 MP3 元数据写入来加快转换。需要重新生成已存在章节时，勾选“覆盖重转”。音色下拉框会优先显示中文说明，内部仍使用 Edge TTS 的真实音色 ID。

GUI 会记住上次使用的音色、输出目录、语速、音量、音调、质量选项、封面、背景音乐目录和 Calibre 路径；不会自动记住当前电子书路径，避免下次打开时误处理旧文件。

勾选“生成 M4B”后，每本书转换完成会在书名输出目录里额外生成一个整本 `.m4b` 文件，并写入章节标题元数据；如果设置了封面图片，也会尝试写入封面。

输出目录会自动按书名创建子文件夹。例如输出根目录是 `output_audio`，电子书书名是 `示例小说`，最终音频会保存到：

```text
output_audio/示例小说/
```

每本书输出目录会额外写入 `conversion_summary.json`，记录本次转换的源文件、书名作者、参数、成功/失败/跳过统计、失败章节和 M4B 路径，便于排错和复盘。

转换过程中可以点击“暂停”，当前正在转换的章节会继续完成，后续章节会等待；点击“继续”后恢复处理。点击“取消”会等待当前章节收尾，然后停止后续章节或后续队列任务。

批量处理多本书时，可以点击“批量添加”选择多个 EPUB/TXT/DOCX/MOBI/AZW3 文件，再点击“开始队列”。队列会按顺序一本一本转换，共用当前音色、语速、音量、音调、输出根目录、背景音乐和质量设置；每本书仍会自动输出到自己的书名文件夹。队列列表会显示待转换、转换中、已完成、失败和已取消状态。

如果有章节失败，界面会显示失败数量，并启用“重试失败”按钮。重试时会复用上次设置，已生成的章节默认自动跳过；如果要重新生成已有章节，请勾选“覆盖重转”。

选择电子书后，右侧会显示章节预览。双击章节行可以在“转换/跳过”之间切换；开始转换时只处理标记为“是”的章节。转换过程中，状态列会显示待转换、转换中、已完成、已跳过、失败或已取消。

GUI 里也有“环境检查”按钮，可检查 Python、依赖包、ffmpeg 和可选的 Calibre `ebook-convert` 是否可用。如果填写了 Calibre 路径，环境检查会优先检测这个路径。Calibre 路径行提供“下载”按钮，会打开官方 Windows 64 位下载页。

每次开始转换前会先做短文本音色自检；如果所选音色不可用，会直接停止并在日志里显示原因。

转换日志会同步显示在界面右侧，并追加写入项目根目录的每日日志文件：

```text
日志YYYYMMDD.txt
```

例如 `日志20260513.txt`。

## Windows 打包

如果要生成可分发的 Windows 目录版程序，先安装 PyInstaller：

```shell
.venv\Scripts\python.exe -m pip install pyinstaller
```

然后双击 `build_windows.bat`，或运行：

```shell
pdm build-windows
```

生成结果位于：

```text
dist/BookVoiceStudio/
```

默认打包不内置 Calibre。需要让打包版直接支持 MOBI/AZW3 时，可以让用户安装 Calibre，也可以在 `dist/BookVoiceStudio/` 旁放置 `calibre/ebook-convert.exe`，或在 GUI 里手动选择 Calibre 路径。重新分发 Calibre 时需单独遵守 Calibre 的 GPL 许可证要求。

## 产品文档

普通用户请先看 [使用说明书](docs/user-guide.md)。

产品升级策划文档位于 [docs/product/README.md](docs/product/README.md)，覆盖 PRD、MVP 范围、Backlog、GUI 交互、电子书解析、音频生成、异常日志和版本路线图。

项目来源、改造说明和许可证注意事项见 [NOTICE.md](NOTICE.md)。

运行测试：

```shell
pdm start example/mc.epub
```

可以使用这个命令查看支持哪些语音：

```shell
pdm run edge-tts --list-voices
```

添加背景音乐

```
pdm start -b bg -v zh-CN-YunjianNeural example/mc.epub
```

## 其他

可以配合 <https://github.com/freeok/so-novel> 下载小说，然后用本工具转换为有声读物。
