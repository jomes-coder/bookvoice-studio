# Desktop GUI and Voice Selection Design

## Goal

Add a source-run desktop GUI for epub2mp3 that lets users choose an EPUB file, voice, output directory, optional background music directory, retry count, concurrency, and speed-related post-processing options without typing CLI commands.

## Scope

This first version is a Python source-run desktop application, launched from PDM. It does not package a Windows executable, add pause or cancellation, persist profiles, or add advanced chapter splitting.

The GUI must preserve the existing CLI workflow while making the common path easier:

- Select an EPUB file.
- Select a built-in common voice or refresh the full Edge TTS voice list.
- Select an output directory.
- Optionally select a background music directory.
- Set retry count.
- Set maximum concurrent chapter conversions.
- Toggle high-quality MP3 transcoding.
- Toggle lyric tag writing.
- Start conversion and read logs in the window.

## Architecture

Use Tkinter for the desktop GUI because it is available in the Python standard library and keeps the source-run version lightweight. Add `src/epub2mp3/gui.py` for the window and keep conversion behavior in reusable non-GUI modules.

Refactor current conversion code so CLI and GUI share the same core:

- `EpubToMP3Converter` remains the conversion engine.
- Logging becomes injectable through a callable, defaulting to `print`.
- Conversion options become explicit constructor or method parameters.
- Shared validation helpers protect both CLI and GUI from invalid inputs.
- Voice list helpers provide built-in voices and refresh the complete Edge TTS list.

## GUI Layout

Use a two-column desktop layout.

Left column: settings and commands.

- EPUB file path entry with browse button.
- Voice combobox populated with common built-in voices.
- Refresh voices button.
- Output directory entry with browse button.
- Background music directory entry with browse button and clear button.
- Retry count numeric field, default `3`.
- Concurrent chapters numeric field, default `3`.
- High-quality transcode checkbox, default enabled.
- Write lyrics checkbox, default enabled.
- Start conversion button.

Right column: read-only conversion log.

- Shows validation errors.
- Shows voice refresh status.
- Shows each chapter conversion message.
- Shows final success or failure summary.

The window must stay responsive while conversion runs. Conversion runs on a background thread; GUI log updates are marshalled back onto the Tkinter event loop.

## Voice Selection

Ship with a small built-in voice list focused on common Chinese voices:

- `zh-CN-YunxiaNeural`
- `zh-CN-YunxiNeural`
- `zh-CN-YunjianNeural`
- `zh-CN-XiaoxiaoNeural`
- `zh-CN-XiaoyiNeural`
- `zh-CN-YunyangNeural`

The Refresh voices button calls `edge_tts.list_voices()` asynchronously in a background thread. On success, update the combobox with all returned short names. On failure, keep the built-in list and append a readable error to the log.

## Conversion Behavior

Add a configurable concurrency limit. The converter should process chapters with an `asyncio.Semaphore` instead of launching all chapter tasks without a bound. Default concurrency is `3`.

Add post-processing options:

- `enable_high_quality`: when true, run `convert_mp3_high_quality`.
- `enable_lyrics`: when true, run `write_lyrics_to_mp3`.

Background music remains optional. If a valid background music directory is selected, keep the existing behavior of choosing a random MP3 per chapter.

Fix the CLI background music argument bug by passing `args.bg_dir` directly. Update the README background music example to use `-v` for voice selection instead of `-o`.

## Validation

Shared validation should reject:

- Missing EPUB path.
- EPUB path that does not exist.
- EPUB path that is not a file.
- Empty output directory.
- Retry count less than `1`.
- Concurrency less than `1`.
- Background music path that is present but not a directory.

GUI validation errors appear in the log and do not start conversion.

CLI validation errors are reported as readable errors.

## Error Handling

Chapter-level conversion failures should still be collected and reported instead of stopping the entire book. Temporary MP3 files created during chapter processing should be removed on failure when they still exist.

Voice refresh failures must not block conversion with built-in voices.

FFmpeg post-processing failures should be logged. The first version may preserve the current behavior of continuing when transcode or lyric writing fails, but the log message must be visible in the GUI.

## Tests

Add focused tests for non-GUI behavior:

- Built-in voice list includes expected voice names.
- Voice short names are extracted from Edge TTS voice dictionaries.
- Validation accepts valid inputs.
- Validation rejects invalid EPUB path, output directory, retry count, concurrency, and background music directory.
- Converter respects the concurrency limit when processing chapters.
- Converter skips high-quality transcode and lyric writing when the options are disabled.

Add light GUI tests only where they do not require interactive automation, such as verifying that the GUI module exposes the launch function. Avoid brittle pixel or click tests for Tkinter in the first version.

## Launch Commands

Keep the existing CLI command:

```shell
pdm start example/mc.epub
```

Add a GUI command:

```shell
pdm gui
```

The GUI command launches `python -m epub2mp3.gui`.
