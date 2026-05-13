import argparse
import asyncio
import os
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    __package__ = "bookvoice"

from .branding import PRODUCT_NAME
from .converter import EpubToMP3Converter
from .health import format_health_checks, run_environment_checks
from .options import (
    DEFAULT_MAX_CONCURRENCY,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PITCH,
    DEFAULT_RATE,
    DEFAULT_RETRIES,
    DEFAULT_VOLUME,
    DEFAULT_VOICE,
    ConversionOptions,
    validate_conversion_inputs,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            f"{PRODUCT_NAME}: 将 EPUB/TXT/DOCX/MOBI/AZW3 电子书转换为 MP3 音频文件，"
            "每章一个文件。MOBI/AZW3 需要本机安装 Calibre ebook-convert，"
            "且不支持 DRM 加密文件。"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "epub_path",
        type=str,
        nargs="?",
        help="要转换的 EPUB/TXT/DOCX/MOBI/AZW3 文件的路径。",
    )
    parser.add_argument(
        "-v",
        "--voice",
        type=str,
        default=DEFAULT_VOICE,
        help=(
            "用于文本转语音的 Edge TTS 声音。\n"
            "例如: zh-CN-YunxiNeural, en-US-AriaNeural\n"
            "使用 'edge-tts --list-voices' 命令查看所有可用声音。\n"
            f"默认值: {DEFAULT_VOICE}"
        ),
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default=DEFAULT_OUTPUT_DIR,
        help=f"保存生成的 MP3 文件的目录。\n默认值: {DEFAULT_OUTPUT_DIR}",
    )
    parser.add_argument(
        "-r",
        "--retries",
        type=int,
        default=DEFAULT_RETRIES,
        help=f"转换失败时的最大重试次数。\n默认值: {DEFAULT_RETRIES}",
    )
    parser.add_argument(
        "-b",
        "--bg-dir",
        type=str,
        help="背景音乐文件所在目录，如果指定，程序会随机选择一个背景音乐添加到每个章节的音频中。\n默认不添加背景音乐。",
    )
    parser.add_argument(
        "-c",
        "--concurrency",
        type=int,
        default=DEFAULT_MAX_CONCURRENCY,
        help=f"同时转换的最大章节数。\n默认值: {DEFAULT_MAX_CONCURRENCY}",
    )
    parser.add_argument(
        "--no-high-quality",
        action="store_true",
        help="跳过 320kbps/48kHz 高质量转码，加快转换速度。",
    )
    parser.add_argument(
        "--no-lyrics",
        action="store_true",
        help="跳过歌词标签写入，加快转换速度。",
    )
    parser.add_argument(
        "--rate",
        type=str,
        default=DEFAULT_RATE,
        help=f"语速，例如 -20%%, +0%%, +15%%。默认值: {DEFAULT_RATE.replace('%', '%%')}",
    )
    parser.add_argument(
        "--volume",
        type=str,
        default=DEFAULT_VOLUME,
        help=f"音量，例如 -10%%, +0%%, +10%%。默认值: {DEFAULT_VOLUME.replace('%', '%%')}",
    )
    parser.add_argument(
        "--pitch",
        type=str,
        default=DEFAULT_PITCH,
        help=f"音调，例如 -5Hz, +0Hz, +5Hz。默认值: {DEFAULT_PITCH}",
    )
    parser.add_argument(
        "--cover",
        dest="cover_path",
        type=str,
        help="封面图片路径，支持 JPG/JPEG/PNG，会写入章节 MP3 和 M4B。",
    )
    parser.add_argument(
        "--no-mp3-metadata",
        action="store_true",
        help="跳过 MP3 章节标题、书名、作者和封面元数据写入。",
    )
    parser.add_argument(
        "--m4b",
        action="store_true",
        help="转换完成后生成整本 M4B 有声书文件。",
    )
    parser.add_argument(
        "--overwrite-existing",
        action="store_true",
        help="覆盖已存在的章节 MP3，重新转换同名章节。",
    )
    parser.add_argument(
        "--ebook-convert",
        dest="ebook_convert_path",
        type=str,
        help=(
            "Calibre ebook-convert.exe 路径。"
            "未指定时会自动查找程序旁 calibre 目录、PATH 和常见安装目录。"
        ),
    )
    parser.add_argument(
        "--check-env",
        action="store_true",
        help="检查 Python、依赖包和 ffmpeg 是否可用，然后退出。",
    )
    return parser


def options_from_args(args: argparse.Namespace) -> ConversionOptions:
    return ConversionOptions(
        epub_path=args.epub_path,
        output_dir=args.output_dir,
        voice=args.voice,
        retries=args.retries,
        bg_dir=args.bg_dir,
        max_concurrency=args.concurrency,
        enable_high_quality=not args.no_high_quality,
        enable_lyrics=not args.no_lyrics,
        rate=args.rate,
        volume=args.volume,
        pitch=args.pitch,
        cover_path=args.cover_path,
        enable_mp3_metadata=not args.no_mp3_metadata,
        export_m4b=args.m4b,
        overwrite_existing=args.overwrite_existing,
        ebook_convert_path=args.ebook_convert_path,
    )


def converter_from_options(options: ConversionOptions) -> EpubToMP3Converter:
    return EpubToMP3Converter(
        voice=options.voice,
        output_dir=options.output_dir,
        max_retries=options.retries,
        bg_dir=options.bg_dir,
        max_concurrency=options.max_concurrency,
        enable_high_quality=options.enable_high_quality,
        enable_lyrics=options.enable_lyrics,
        rate=options.rate,
        volume=options.volume,
        pitch=options.pitch,
        selected_chapter_indexes=options.selected_chapter_indexes,
        cover_path=options.cover_path,
        enable_mp3_metadata=options.enable_mp3_metadata,
        export_m4b=options.export_m4b,
        overwrite_existing=options.overwrite_existing,
        ebook_convert_path=options.ebook_convert_path,
    )


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.check_env:
        print(
            format_health_checks(
                run_environment_checks(ebook_convert_path=args.ebook_convert_path)
            )
        )
        return

    options = options_from_args(args)
    validation_errors = validate_conversion_inputs(options)
    if validation_errors:
        for error in validation_errors:
            print(f"错误: {error}")
        return

    converter = converter_from_options(options)
    try:
        result = asyncio.run(converter.convert_epub(options.epub_path))
        print("\n转换完成！")
        print(
            "结果: "
            f"总章节 {result.total}, "
            f"成功 {result.completed}, "
            f"跳过 {result.skipped}, "
            f"失败 {result.failed}"
        )
        if result.m4b_path:
            print(f"M4B 文件: {result.m4b_path}")
        print(f"所有音频文件已保存到目录: {result.output_dir}")
    except FileNotFoundError as exc:
        print(f"\n错误: {exc}")
    except ValueError as exc:
        print(f"\n错误: {exc}")
    except Exception as exc:
        print(f"\n转换过程中出现未知错误: {exc}")


if __name__ == "__main__":
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    main()
