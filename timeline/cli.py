from __future__ import annotations

import argparse
import csv
import io
import sys
from pathlib import Path
from typing import List, NoReturn, Optional

from .model import (
    TimelineError,
    demo_events,
    filter_events,
    paginate,
    read_csv,
)
from .render import render_timeline


class _ArgumentParser(argparse.ArgumentParser):
    """把 argparse 的英文错误提示改写为中文，并统一返回退出码 2。"""

    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        print("参数错误：{}".format(message), file=sys.stderr)
        raise SystemExit(2)


def _build_parser() -> argparse.ArgumentParser:
    """构造命令行解析器。"""
    parser = _ArgumentParser(
        prog="timeline",
        description="历史事件时间轴生成器：把 CSV 整理成可打印的 A4 时间轴",
    )
    parser.add_argument(
        "-i", "--input", metavar="CSV", help="输入 CSV 文件（表头 year,title,description,category）"
    )
    parser.add_argument(
        "-o",
        "--output",
        default="timeline.html",
        metavar="HTML",
        help="输出 HTML 文件（默认 timeline.html）",
    )
    parser.add_argument("--start", metavar="YEAR", help="起始年份（含）")
    parser.add_argument("--end", metavar="YEAR", help="结束年份（含）")
    parser.add_argument("--category", metavar="NAME", help="按分类精确筛选")
    parser.add_argument(
        "--title", default="历史事件时间轴", help="页面标题（默认：历史事件时间轴）"
    )
    parser.add_argument(
        "--per-page",
        dest="per_page",
        default="6",
        metavar="N",
        help="每页事件数，范围 1..30（默认 6）",
    )

    subparsers = parser.add_subparsers(dest="command")
    demo = subparsers.add_parser("demo", help="写出内置示例 CSV")
    demo.add_argument(
        "-o",
        "--output",
        dest="demo_output",
        default="events.csv",
        metavar="CSV",
        help="示例 CSV 输出路径（默认 events.csv）",
    )
    return parser


def _parse_int_option(value: Optional[str], name: str) -> Optional[int]:
    """把命令行字符串转换为整数，失败时抛出中文错误。"""
    if value is None:
        return None
    if not isinstance(value, str):
        raise TimelineError("{} 必须是整数".format(name))
    text = value.strip()
    if not text:
        raise TimelineError("{} 不能为空".format(name))
    try:
        return int(text)
    except ValueError as exc:
        raise TimelineError(
            "{} 必须是整数，实际值为 {!r}".format(name, value)
        ) from exc


def _write_text(path: Path, text: str, encoding: str = "utf-8") -> None:
    """写出文本文件，并把常见文件系统错误转换为清晰的中文提示。"""
    target = Path(path)
    try:
        target.write_text(text, encoding=encoding)
    except FileNotFoundError as exc:
        raise FileNotFoundError("写入失败，目录不存在：{}".format(target)) from exc
    except IsADirectoryError as exc:
        raise IsADirectoryError("写入失败，目标是目录：{}".format(target)) from exc
    except PermissionError as exc:
        raise PermissionError("写入失败，没有权限：{}".format(target)) from exc
    except OSError as exc:
        raise OSError("写入失败：{}（{}）".format(target, exc)) from exc


def _demo_csv_text() -> str:
    """生成示例 CSV 文本（UTF-8 无 BOM 内容）。"""
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["year", "title", "description", "category"])
    for event in demo_events():
        writer.writerow(
            [event.year, event.title, event.description, event.category]
        )
    return buffer.getvalue()


def _run_demo(output: Path) -> int:
    """执行 demo 子命令：写出内置示例 CSV。"""
    events = demo_events()
    _write_text(output, _demo_csv_text(), encoding="utf-8-sig")
    print("已写出示例 CSV：{}（{} 个事件）".format(output, len(events)))
    return 0


def _run_render(args: argparse.Namespace) -> int:
    """执行主命令：读取 CSV、筛选并渲染 HTML。"""
    input_value = getattr(args, "input", None)
    if not input_value:
        raise TimelineError("请使用 -i/--input 指定 CSV 输入文件")

    start = _parse_int_option(getattr(args, "start", None), "--start")
    end = _parse_int_option(getattr(args, "end", None), "--end")
    per_page = _parse_int_option(getattr(args, "per_page", None), "--per-page")
    if per_page is None:
        raise TimelineError("--per-page 不能为空")

    input_path = Path(input_value)
    all_events = read_csv(input_path)
    events = filter_events(all_events, start=start, end=end, category=args.category)

    html_text = render_timeline(
        events, title=args.title, per_page=per_page
    )
    output_path = Path(args.output)
    _write_text(output_path, html_text)

    pages = 1 if not events else 1 + len(paginate(events, per_page))
    print(
        "已生成 {}（{} 个事件，{} 页）".format(
            output_path, len(events), pages
        )
    )
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    """命令行入口，返回进程退出码：0 成功、1 文件错误、2 参数或数据错误。"""
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        if code is None:
            return 0
        if isinstance(code, int):
            return code
        return 2

    try:
        if args.command == "demo":
            return _run_demo(Path(args.demo_output))
        return _run_render(args)
    except TimelineError as exc:
        print("错误：{}".format(exc), file=sys.stderr)
        return 2
    except (FileNotFoundError, IsADirectoryError, PermissionError) as exc:
        print("文件错误：{}".format(exc), file=sys.stderr)
        return 1
    except OSError as exc:
        print("文件错误：{}".format(exc), file=sys.stderr)
        return 1
