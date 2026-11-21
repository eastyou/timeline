from __future__ import annotations

import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from timeline.cli import main
from timeline.model import read_csv


_CSV = (
    "year,title,description,category\n"
    "1919,五四运动,北京学生游行示威,政治\n"
    "1921,中国共产党成立,中共一大召开,政治\n"
    "1937,七七事变,全民族抗战爆发,战争\n"
)


def _run(argv: list[str]) -> tuple[int, str, str]:
    """执行 CLI 并收集退出码、标准输出与标准错误。"""
    stdout = io.StringIO()
    stderr = io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = main(argv)
    return code, stdout.getvalue(), stderr.getvalue()


def _write_csv(path: Path, text: str = _CSV, encoding: str = "utf-8") -> None:
    path.write_text(text, encoding=encoding)


class DemoCommandTests(unittest.TestCase):
    def test_demo_writes_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "events.csv"
            code, stdout, _ = _run(["demo", "-o", str(output)])
            self.assertEqual(code, 0)
            self.assertTrue(output.exists())
            self.assertIn("12", stdout)
            self.assertEqual(len(read_csv(output)), 12)

    def test_demo_uses_utf8_sig(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "events.csv"
            self.assertEqual(_run(["demo", "-o", str(output)])[0], 0)
            self.assertTrue(output.read_bytes().startswith(b"\xef\xbb\xbf"))

    def test_demo_missing_directory_returns_one(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "missing" / "events.csv"
            code, _, stderr = _run(["demo", "-o", str(output)])
            self.assertEqual(code, 1)
            self.assertIn("写入失败", stderr)


class RenderCommandTests(unittest.TestCase):
    def test_render_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "events.csv"
            output = Path(tmp) / "timeline.html"
            _write_csv(csv_path)
            code, _, _ = _run(["-i", str(csv_path), "-o", str(output)])
            self.assertEqual(code, 0)
            self.assertTrue(output.exists())
            html = output.read_text(encoding="utf-8")
            self.assertIn("五四运动", html)
            self.assertIn("七七事变", html)

    def test_render_stdout_message(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "events.csv"
            output = Path(tmp) / "timeline.html"
            _write_csv(csv_path)
            code, stdout, _ = _run(["-i", str(csv_path), "-o", str(output)])
            self.assertEqual(code, 0)
            self.assertIn("已生成", stdout)
            self.assertIn("3 个事件", stdout)
            self.assertIn("2 页", stdout)

    def test_render_default_output_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "events.csv"
            _write_csv(csv_path)
            previous = Path.cwd()
            os.chdir(tmp)
            try:
                code, _, _ = _run(["-i", str(csv_path)])
            finally:
                os.chdir(previous)
            self.assertEqual(code, 0)
            self.assertTrue((Path(tmp) / "timeline.html").exists())

    def test_render_custom_title(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "events.csv"
            output = Path(tmp) / "out.html"
            _write_csv(csv_path)
            code, _, _ = _run(
                ["-i", str(csv_path), "-o", str(output), "--title", "自定义标题"]
            )
            self.assertEqual(code, 0)
            self.assertIn("<h1>自定义标题</h1>", output.read_text(encoding="utf-8"))

    def test_render_per_page_one(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "events.csv"
            output = Path(tmp) / "out.html"
            _write_csv(csv_path)
            code, stdout, _ = _run(
                ["-i", str(csv_path), "-o", str(output), "--per-page", "1"]
            )
            self.assertEqual(code, 0)
            self.assertIn("4 页", stdout)

    def test_render_utf8_sig_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "events.csv"
            output = Path(tmp) / "out.html"
            _write_csv(csv_path, encoding="utf-8-sig")
            code, _, _ = _run(["-i", str(csv_path), "-o", str(output)])
            self.assertEqual(code, 0)
            self.assertIn("五四运动", output.read_text(encoding="utf-8"))

    def test_render_empty_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "events.csv"
            output = Path(tmp) / "out.html"
            _write_csv(csv_path, "year,title\n")
            code, stdout, _ = _run(["-i", str(csv_path), "-o", str(output)])
            self.assertEqual(code, 0)
            html = output.read_text(encoding="utf-8")
            self.assertIn("暂无符合条件的历史事件", html)
            self.assertIn("0 个事件，1 页", stdout)


class FilterCommandTests(unittest.TestCase):
    def test_category_filter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "events.csv"
            output = Path(tmp) / "out.html"
            _write_csv(csv_path)
            code, _, _ = _run(
                ["-i", str(csv_path), "-o", str(output), "--category", "战争"]
            )
            self.assertEqual(code, 0)
            html = output.read_text(encoding="utf-8")
            self.assertIn("七七事变", html)
            self.assertNotIn("五四运动", html)

    def test_year_range_filter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "events.csv"
            output = Path(tmp) / "out.html"
            _write_csv(csv_path)
            code, _, _ = _run(
                [
                    "-i",
                    str(csv_path),
                    "-o",
                    str(output),
                    "--start",
                    "1920",
                    "--end",
                    "1930",
                ]
            )
            self.assertEqual(code, 0)
            html = output.read_text(encoding="utf-8")
            self.assertIn("中国共产党成立", html)
            self.assertNotIn("五四运动", html)

    def test_filter_no_match_generates_empty_page(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "events.csv"
            output = Path(tmp) / "out.html"
            _write_csv(csv_path)
            code, stdout, _ = _run(
                ["-i", str(csv_path), "-o", str(output), "--category", "不存在"]
            )
            self.assertEqual(code, 0)
            self.assertIn("暂无符合条件的历史事件", output.read_text(encoding="utf-8"))
            self.assertIn("0 个事件，1 页", stdout)


class CliErrorTests(unittest.TestCase):
    def test_missing_input_returns_two(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            code, _, stderr = _run(["-o", str(Path(tmp) / "out.html")])
            self.assertEqual(code, 2)
            self.assertIn("指定 CSV", stderr)

    def test_nonexistent_input_returns_one(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            code, _, stderr = _run(
                ["-i", str(Path(tmp) / "missing.csv"), "-o", str(Path(tmp) / "out.html")]
            )
            self.assertEqual(code, 1)
            self.assertIn("文件不存在", stderr)

    def test_per_page_zero_returns_two(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "events.csv"
            _write_csv(csv_path)
            code, _, stderr = _run(
                ["-i", str(csv_path), "-o", str(Path(tmp) / "out.html"), "--per-page", "0"]
            )
            self.assertEqual(code, 2)
            self.assertIn("每页事件数", stderr)

    def test_per_page_too_large_returns_two(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "events.csv"
            _write_csv(csv_path)
            code, _, stderr = _run(
                ["-i", str(csv_path), "-o", str(Path(tmp) / "out.html"), "--per-page", "31"]
            )
            self.assertEqual(code, 2)
            self.assertIn("每页事件数", stderr)

    def test_per_page_not_number_returns_two(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "events.csv"
            _write_csv(csv_path)
            code, _, stderr = _run(
                ["-i", str(csv_path), "-o", str(Path(tmp) / "out.html"), "--per-page", "abc"]
            )
            self.assertEqual(code, 2)
            self.assertIn("必须是整数", stderr)

    def test_start_not_number_returns_two(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "events.csv"
            _write_csv(csv_path)
            code, _, stderr = _run(
                ["-i", str(csv_path), "-o", str(Path(tmp) / "out.html"), "--start", "abc"]
            )
            self.assertEqual(code, 2)
            self.assertIn("--start", stderr)

    def test_start_after_end_returns_two(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "events.csv"
            _write_csv(csv_path)
            code, _, stderr = _run(
                [
                    "-i",
                    str(csv_path),
                    "-o",
                    str(Path(tmp) / "out.html"),
                    "--start",
                    "1949",
                    "--end",
                    "1919",
                ]
            )
            self.assertEqual(code, 2)
            self.assertIn("起始年份不能大于结束年份", stderr)

    def test_output_directory_missing_returns_one(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "events.csv"
            _write_csv(csv_path)
            code, _, stderr = _run(
                ["-i", str(csv_path), "-o", str(Path(tmp) / "missing" / "out.html")]
            )
            self.assertEqual(code, 1)
            self.assertIn("写入失败", stderr)

    def test_unknown_option_returns_two(self) -> None:
        code, _, stderr = _run(["--not-a-real-option"])
        self.assertEqual(code, 2)
        self.assertIn("参数错误", stderr)

    def test_help_returns_zero(self) -> None:
        code, stdout, _ = _run(["--help"])
        self.assertEqual(code, 0)
        self.assertIn("历史事件时间轴生成器", stdout)

    def test_no_arguments_returns_two(self) -> None:
        code, _, stderr = _run([])
        self.assertEqual(code, 2)
        self.assertIn("指定 CSV", stderr)


if __name__ == "__main__":
    unittest.main()
