# Product P0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the first productized EPUB workflow: book metadata, automatic book output folders, speech parameters, visible progress, output-folder access, and updated logs/docs.

**Architecture:** Add a focused `book.py` module that converts EPUB input into a `ParsedBook` model used by CLI and GUI. Extend `ConversionOptions` and `EpubToMP3Converter` with speech parameters and progress callbacks while keeping the existing conversion engine shared by CLI and GUI.

**Tech Stack:** Python 3.12, Tkinter, asyncio, unittest, ebooklib, BeautifulSoup, edge-tts, ffmpeg helpers.

---

## File Structure

- Create: `src/epub2mp3/book.py`
  - Owns book metadata, parsed chapter model, EPUB parsing, output directory naming, and legacy chapter tuple conversion.
- Modify: `src/epub2mp3/options.py`
  - Adds rate, volume, pitch, and resolved output directory fields plus validation.
- Modify: `src/epub2mp3/main.py`
  - Uses `ParsedBook`, writes into the book output directory, passes speech parameters to Edge TTS, and emits progress callbacks.
- Modify: `src/epub2mp3/gui.py`
  - Adds speech controls, output directory opening, progress labels, and uses actual book output directory.
- Modify: `src/epub2mp3/run_log.py`
  - Records book metadata and speech parameters.
- Modify: `src/epub2mp3/voices.py`
  - Makes voice self-test use speech parameters.
- Modify: `README.md`
  - Documents book folders and speech parameters.
- Create: `tests/test_book.py`
  - Tests metadata fallback, filename sanitizing, output path creation, chapter filtering, and EPUB parsing.
- Modify: existing tests
  - Update options, converter, CLI parser, GUI import/layout, run log, and voice tests.

## Tasks

### Task 1: Book Model and Output Directory

- [x] Write tests in `tests/test_book.py` for `sanitize_book_folder_name`, `build_book_output_dir`, metadata fallback, and parsed chapter tuples.
- [x] Run `python -m unittest tests.test_book -v` and confirm import failures for the new module.
- [x] Implement `src/epub2mp3/book.py` with `BookMetadata`, `ParsedChapter`, `ParsedBook`, `sanitize_book_folder_name`, `build_book_output_dir`, and `chapters_as_tuples`.
- [x] Run `python -m unittest tests.test_book -v` and confirm the tests pass.

### Task 2: EPUB Parsing

- [x] Add an EPUB fixture builder inside `tests/test_book.py` using `ebooklib.epub.EpubBook`.
- [x] Test that `parse_epub_book()` reads title/author, follows spine order, skips empty pages, uses toc titles where available, and produces clean chapter text.
- [x] Run the test and confirm it fails because `parse_epub_book()` is missing.
- [x] Implement `parse_epub_book()` in `book.py`, reusing BeautifulSoup cleanup and safe fallbacks.
- [x] Run `python -m unittest tests.test_book -v`.

### Task 3: Converter Uses ParsedBook and Book Output Folder

- [x] Add converter tests proving output files are written under `output_root/book_title`.
- [x] Run the specific converter test and confirm it fails.
- [x] Update `EpubToMP3Converter.convert_epub()` to parse the book once, set `self.actual_output_dir`, ensure that directory exists, and process `ParsedChapter` objects.
- [x] Preserve `get_chapters()` compatibility by delegating to `parse_epub_book().chapters_as_tuples()`.
- [x] Run converter and book tests.

### Task 4: Speech Parameters

- [x] Add option and parser tests for `rate`, `volume`, and `pitch`.
- [x] Run the tests and confirm they fail.
- [x] Extend `ConversionOptions`, parser flags, `EpubToMP3Converter.__init__`, `text_to_speech_with_retry()`, and `verify_voice_can_speak()`.
- [x] Run CLI, options, converter, and voice tests.

### Task 5: GUI Controls and Progress

- [x] Add import/layout tests for speech control row ordering and progress labels/constants.
- [x] Run GUI tests and confirm failure for missing constants.
- [x] Add GUI variables and controls for rate/volume/pitch, progress summary, and an output-folder button.
- [x] Pass speech parameters into conversion and self-test.
- [x] Update progress state from converter callbacks.
- [x] Run GUI tests.

### Task 6: Logs and Documentation

- [x] Update run log tests to assert book output directory and speech parameters are recorded.
- [x] Run run log tests and confirm failure.
- [x] Update `DailyLogWriter.write_run_header()`.
- [x] Update `README.md` with book folders and speech parameters.
- [x] Run run log tests.

### Task 7: Full Verification

- [x] Run `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m unittest discover -s tests -v`.
- [x] Run `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m compileall -q src tests`.
- [x] Report exactly which P0 capabilities were implemented and which product-doc capabilities remain planned for later versions.
