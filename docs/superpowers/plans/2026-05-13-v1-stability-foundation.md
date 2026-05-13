# V1 Stability Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Continue toward a stable 1.0 by adding TXT support, generic book parsing, structured conversion summaries, and retry-failed workflow hooks.

**Architecture:** Keep the shared conversion engine and extend the existing `book.py` parser module with a format dispatcher and TXT parser. Return a `ConversionResult` from conversion so CLI and GUI can report success, skipped, and failed chapters consistently.

**Tech Stack:** Python 3.12, Tkinter, asyncio, unittest, ebooklib, BeautifulSoup, Edge TTS.

---

## Task 1: Generic Book Parser and TXT Support

- [x] Add tests for TXT chapter splitting, encoding fallback, and unsupported format errors.
- [x] Implement `parse_book()` and `parse_txt_book()` in `src/epub2mp3/book.py`.
- [x] Update `utils.get_chapters()` and converter parsing to use `parse_book()`.

## Task 2: Supported Format Validation and UI Entry

- [x] Add validation tests for unsupported ebook extensions.
- [x] Update `ConversionOptions` validation messages to refer to ebook files instead of EPUB only.
- [x] Update CLI help and GUI file picker for EPUB/TXT.

## Task 3: Conversion Result Summary

- [x] Add tests for returned total/completed/skipped/failed counts.
- [x] Add `ConversionResult` and make `convert_epub()` return it.
- [x] Log and display summary in CLI/GUI.

## Task 4: Retry Failed Workflow Hook

- [x] Add GUI layout constant and button for retrying failed chapters.
- [x] Store last successful options and enable retry button when a conversion completed with failures.
- [x] Retry reuses the same options; existing completed files are skipped, so failed chapters are regenerated.

## Task 5: Verification

- [x] Run full unit tests.
- [x] Run compileall.
- [x] Update README with TXT support and retry behavior.

