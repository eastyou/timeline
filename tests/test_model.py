from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from timeline.model import (
    Event,
    TimelineError,
    demo_events,
    filter_events,
    paginate,
    parse_csv_text,
    position_ratio,
    read_csv,
    year_range,
)


def _events() -> list[Event]:
    return [
        Event(1919, "五四运动", "北京学生游行示威", "政治"),
        Event(1921, "中国共产党成立", "中共一大召开", "政治"),
        Event(1937, "七七事变", "全民族抗战爆发", "战争"),
        Event(1949, "新中国成立", "开国大典", "政治"),
    ]


class ParseCsvTests(unittest.TestCase):
    def test_parse_basic_fields(self) -> None:
        events = parse_csv_text("year,title,description,category\n1919,五四运动,学生游行,政治\n")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0], Event(1919, "五四运动", "学生游行", "政治"))

    def test_parse_returns_sorted_by_year(self) -> None:
        text = "year,title\n1949,乙\n1919,甲\n1921,丙\n"
        self.assertEqual([event.year for event in parse_csv_text(text)], [1919, 1921, 1949])

    def test_parse_same_year_sorted_by_title(self) -> None:
        text = "year,title\n1919,B event\n1919,A event\n"
        self.assertEqual(
            [event.title for event in parse_csv_text(text)],
            ["A event", "B event"],
        )

    def test_parse_header_order_flexible(self) -> None:
        text = "title,category,year,description\n五四运动,政治,1919,学生游行\n"
        event = parse_csv_text(text)[0]
        self.assertEqual(event.year, 1919)
        self.assertEqual(event.title, "五四运动")
        self.assertEqual(event.category, "政治")
        self.assertEqual(event.description, "学生游行")

    def test_parse_missing_year_header(self) -> None:
        with self.assertRaises(TimelineError) as ctx:
            parse_csv_text("title,description\n五四运动,学生游行\n")
        self.assertIn("year", str(ctx.exception))

    def test_parse_missing_title_header(self) -> None:
        with self.assertRaises(TimelineError) as ctx:
            parse_csv_text("year,description\n1919,学生游行\n")
        self.assertIn("title", str(ctx.exception))

    def test_parse_year_not_number(self) -> None:
        with self.assertRaises(TimelineError) as ctx:
            parse_csv_text("year,title\n19x9,事件\n")
        message = str(ctx.exception)
        self.assertIn("第 2 行", message)
        self.assertIn("year", message)

    def test_parse_year_empty(self) -> None:
        with self.assertRaises(TimelineError) as ctx:
            parse_csv_text("year,title\n,事件\n")
        self.assertIn("year 列不能为空", str(ctx.exception))

    def test_parse_title_blank(self) -> None:
        with self.assertRaises(TimelineError) as ctx:
            parse_csv_text("year,title\n1919,   \n")
        self.assertIn("title 列不能为空", str(ctx.exception))

    def test_parse_title_stripped(self) -> None:
        event = parse_csv_text("year,title\n1919,  五四运动  \n")[0]
        self.assertEqual(event.title, "五四运动")

    def test_parse_ignores_blank_lines(self) -> None:
        text = "year,title\n\n1919,五四运动\n   \n1921,建党\n"
        self.assertEqual(len(parse_csv_text(text)), 2)

    def test_parse_handles_bom(self) -> None:
        text = "\ufeffyear,title\n1919,五四运动\n"
        event = parse_csv_text(text)[0]
        self.assertEqual(event.title, "五四运动")

    def test_parse_without_optional_columns(self) -> None:
        event = parse_csv_text("year,title\n1919,五四运动\n")[0]
        self.assertEqual(event.description, "")
        self.assertEqual(event.category, "")

    def test_parse_empty_text(self) -> None:
        with self.assertRaises(TimelineError):
            parse_csv_text("")

    def test_parse_header_only_returns_empty(self) -> None:
        self.assertEqual(parse_csv_text("year,title\n"), [])

    def test_parse_malformed_quote_raises(self) -> None:
        with self.assertRaises(TimelineError) as ctx:
            parse_csv_text('year,title\n1919,"未闭合\n')
        self.assertIn("CSV", str(ctx.exception))

    def test_parse_extra_cells_ignored(self) -> None:
        event = parse_csv_text("year,title,description,category\n1919,五四运动,描述,政治,多余\n")[0]
        self.assertEqual(event.category, "政治")

    def test_parse_header_case_insensitive(self) -> None:
        event = parse_csv_text("Year,Title\n1919,五四运动\n")[0]
        self.assertEqual(event.title, "五四运动")

    def test_parse_description_and_category_stripped(self) -> None:
        event = parse_csv_text("year,title,description,category\n1919,五四运动,  描述 , 政治 \n")[0]
        self.assertEqual(event.description, "描述")
        self.assertEqual(event.category, "政治")

    def test_parse_negative_year(self) -> None:
        self.assertEqual(parse_csv_text("year,title\n-500,古代事件\n")[0].year, -500)

    def test_parse_returns_event_instances(self) -> None:
        self.assertIsInstance(parse_csv_text("year,title\n1919,事件\n")[0], Event)


class ReadCsvTests(unittest.TestCase):
    def test_read_csv_plain_utf8(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.csv"
            path.write_text("year,title\n1919,五四运动\n", encoding="utf-8")
            self.assertEqual(read_csv(path)[0].title, "五四运动")

    def test_read_csv_utf8_sig(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.csv"
            path.write_text("year,title\n1919,五四运动\n", encoding="utf-8-sig")
            self.assertEqual(read_csv(path)[0].title, "五四运动")

    def test_read_csv_gbk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.csv"
            path.write_text("year,title\n1919,五四运动\n", encoding="gbk")
            self.assertEqual(read_csv(path)[0].title, "五四运动")

    def test_read_csv_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                read_csv(Path(tmp) / "missing.csv")

    def test_read_csv_invalid_encoding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.csv"
            path.write_bytes(b"\xff\xff\xff")
            with self.assertRaises(TimelineError):
                read_csv(path)

    def test_read_csv_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(TimelineError):
                read_csv(Path(tmp))


class FilterTests(unittest.TestCase):
    def test_filter_year_closed_interval(self) -> None:
        result = filter_events(_events(), start=1919, end=1937)
        self.assertEqual([event.year for event in result], [1919, 1921, 1937])

    def test_filter_start_only(self) -> None:
        result = filter_events(_events(), start=1937)
        self.assertEqual([event.year for event in result], [1937, 1949])

    def test_filter_end_only(self) -> None:
        result = filter_events(_events(), end=1921)
        self.assertEqual([event.year for event in result], [1919, 1921])

    def test_filter_category_exact(self) -> None:
        result = filter_events(_events(), category="战争")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].title, "七七事变")

    def test_filter_category_stripped(self) -> None:
        self.assertEqual(len(filter_events(_events(), category="  政治  ")), 3)

    def test_filter_start_after_end(self) -> None:
        with self.assertRaises(TimelineError):
            filter_events(_events(), start=1949, end=1919)

    def test_filter_no_constraints(self) -> None:
        self.assertEqual(len(filter_events(_events())), 4)

    def test_filter_invalid_category_type(self) -> None:
        with self.assertRaises(TimelineError):
            filter_events(_events(), category=123)  # type: ignore[arg-type]

    def test_filter_invalid_start_type(self) -> None:
        with self.assertRaises(TimelineError):
            filter_events(_events(), start="1919")  # type: ignore[arg-type]


class YearRangeAndPositionTests(unittest.TestCase):
    def test_year_range(self) -> None:
        self.assertEqual(year_range(_events()), (1919, 1949))

    def test_year_range_empty(self) -> None:
        with self.assertRaises(TimelineError):
            year_range([])

    def test_position_ratio_start(self) -> None:
        self.assertEqual(position_ratio(1900, 1900, 2000), 0.0)

    def test_position_ratio_middle(self) -> None:
        self.assertAlmostEqual(position_ratio(1950, 1900, 2000), 0.5)

    def test_position_ratio_end(self) -> None:
        self.assertEqual(position_ratio(2000, 1900, 2000), 1.0)

    def test_position_ratio_single_year(self) -> None:
        self.assertEqual(position_ratio(1919, 1919, 1919), 0.5)

    def test_position_ratio_out_of_range(self) -> None:
        with self.assertRaises(TimelineError):
            position_ratio(1899, 1900, 2000)

    def test_position_ratio_start_after_end(self) -> None:
        with self.assertRaises(TimelineError):
            position_ratio(1950, 2000, 1900)

    def test_position_ratio_type_error(self) -> None:
        with self.assertRaises(TimelineError):
            position_ratio(1950.0, 1900, 2000)  # type: ignore[arg-type]


class PaginateTests(unittest.TestCase):
    def test_paginate_even(self) -> None:
        pages = paginate(_events(), 2)
        self.assertEqual(len(pages), 2)
        self.assertEqual(len(pages[0]), 2)

    def test_paginate_remainder(self) -> None:
        pages = paginate(_events(), 3)
        self.assertEqual([len(page) for page in pages], [3, 1])

    def test_paginate_empty(self) -> None:
        self.assertEqual(paginate([], 6), [])

    def test_paginate_per_page_one(self) -> None:
        self.assertEqual(len(paginate(_events(), 1)), 4)

    def test_paginate_zero(self) -> None:
        with self.assertRaises(TimelineError):
            paginate(_events(), 0)

    def test_paginate_too_large(self) -> None:
        with self.assertRaises(TimelineError):
            paginate(_events(), 31)

    def test_paginate_non_integer(self) -> None:
        with self.assertRaises(TimelineError):
            paginate(_events(), "6")  # type: ignore[arg-type]


class DemoTests(unittest.TestCase):
    def test_demo_count(self) -> None:
        self.assertEqual(len(demo_events()), 12)

    def test_demo_sorted(self) -> None:
        years = [event.year for event in demo_events()]
        self.assertEqual(years, sorted(years))

    def test_demo_fields(self) -> None:
        for event in demo_events():
            self.assertTrue(event.title)
            self.assertTrue(event.category)
            self.assertTrue(event.description)


if __name__ == "__main__":
    unittest.main()
