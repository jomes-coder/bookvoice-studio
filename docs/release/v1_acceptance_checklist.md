# BookVoice Studio V1.0 验收清单

本文档用于发布前真实样本验收。每次准备发布 Windows 包或推送稳定版本时，至少完成一轮人工验收，并把异常记录到日志或 issue。

## 1. 样本准备

至少准备以下电子书样本：

- EPUB：带目录、封面、作者元数据的常规小说。
- EPUB：目录缺失或章节标题不规范的电子书。
- TXT：UTF-8 编码小说。
- TXT：GBK 或 GB18030 编码小说。
- DOCX：使用标题样式划分章节的文档。
- MOBI：未加 DRM 的 Kindle 文件，需要 Calibre `ebook-convert` 可用。
- AZW3：未加 DRM 的 Kindle 文件，需要 Calibre `ebook-convert` 可用。

MOBI/AZW3 如果失败，先确认不是 DRM 加密文件，再检查 Calibre 路径。

## 2. GUI 主流程

- 启动桌面 GUI，确认窗口标题为 BookVoice Studio / 书声工坊。
- 点击“环境检查”，确认 Python、依赖包、ffmpeg 状态清晰。
- 选择电子书后，章节预览不会长时间卡住界面。
- 连续选择两本电子书时，只显示最后一次选择的章节预览结果。
- 双击章节行可在“转换/跳过”之间切换。
- 修改音色、语速、音量、音调后开始转换，日志记录参数。
- 点击“暂停”后，当前章节完成，后续章节等待。
- 点击“取消”后，当前章节收尾，后续章节停止。

## 3. 输出结果

- 每本书输出到 `输出目录/书名/`。
- MP3 文件按章节序号排序。
- `conversion_summary.json` 包含源文件、书名、作者、总数、成功、失败、跳过和参数。
- 勾选“写入 MP3 元数据”后，播放器能看到书名、作者或章节标题。
- 勾选“生成 M4B”后生成整本 M4B，并在支持章节的播放器里显示章节。
- 设置封面图片后，MP3 或 M4B 在常见播放器中尽量显示封面。

## 4. 批量队列和任务恢复

- 点击“批量添加”，添加 EPUB/TXT/DOCX/MOBI/AZW3 多本书。
- 队列按顺序转换，不因为单本失败阻塞后续排查。
- 关闭并重新打开 GUI 后，批量队列仍保留。
- 上次关闭时处于“转换中”的任务恢复为“待转换”，避免卡在不可继续状态。
- 点击“清空队列”后，重新启动 GUI 不再显示旧队列。

## 5. Windows 打包

- 执行 `build_windows.bat`，生成 `dist/BookVoiceStudio/`。
- 在干净 Windows 用户环境中启动 `BookVoiceStudio.exe`。
- 首次启动显示使用指南。
- 没有 Calibre 时，MOBI/AZW3 提示清晰，不影响 EPUB/TXT/DOCX。
- 有 Calibre 时，MOBI/AZW3 可进入预览和转换流程。

## 6. 发布判定

满足以下条件才建议发布：

- EPUB/TXT/DOCX 主流程无阻断问题。
- MOBI/AZW3 缺少 Calibre、DRM 或转换失败时有明确提示。
- GUI 不出现控件重叠、按钮不可恢复或日志不可见。
- 转换失败时保留日志和 `conversion_summary.json`。
- Windows 打包产物能在目标机器启动并完成至少一本 EPUB 转换。
