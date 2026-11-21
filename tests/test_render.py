from __future__ import annotations

import unittest

from timeline.model import Event, TimelineError
from timeline.render import render_empty, render_timeline


def _events() -> list[Event]:
    return [
        Event(1919, "五四运动", "北京学生游行示威", "政治"),
        Event(1921, "中国共产党成立", "中共一大召开", "政治"),
        Event(1937, "七七事变", "全民族抗战爆发", "战争"),
        Event(1949, "新中国成立", "开国大典", "政治"),
    ]


class RenderDocumentTests(unittest.TestCase):
    def test_document_structure(self) -> None:
        html = render_timeline(_events())
        self.assertTrue(html.startswith("<!DOCTYPE html>"))
        self.assertIn('<html lang="zh-CN">', html)
        self.assertIn('<meta charset="utf-8">', html)
        self.assertTrue(html.rstrip().endswith("</html>"))

    def test_title_in_document(self) -> None:
        html = render_timeline(_events(), title="中国近现代史")
        self.assertIn("<title>中国近现代史</title>", html)
        self.assertIn("<h1>中国近现代史</h1>", html)

    def test_a4_page_css(self) -> None:
        html = render_timeline(_events())
        self.assertIn("size: A4", html)
        self.assertIn("width: 210mm", html)
        self.assertIn("min-height: 297mm", html)
        self.assertIn("padding: 12mm", html)
        self.assertIn("box-sizing: border-box", html)
        self.assertIn("overflow: hidden", html)

    def test_internal_width_margin(self) -> None:
        self.assertIn("width: 98%", render_timeline(_events()))

    def test_blank_title_defaults(self) -> None:
        self.assertIn("历史事件时间轴", render_timeline(_events(), title="   "))

    def test_title_escaped(self) -> None:
        html = render_timeline(_events(), title="<危险标题>")
        self.assertIn("&lt;危险标题&gt;", html)
        self.assertNotIn("<危险标题>", html)


class RenderScaleTests(unittest.TestCase):
    def test_scale_dots_count(self) -> None:
        html = render_timeline(_events())
        self.assertEqual(html.count('<span class="axis-dot">'), 4)

    def test_scale_start_end_labels(self) -> None:
        html = render_timeline(_events())
        self.assertIn('style="left:0%">1919', html)
        self.assertIn('style="left:100%">1949', html)

    def test_scale_panel_present(self) -> None:
        self.assertIn('<section class="scale-panel">', render_timeline(_events()))

    def test_hide_scale(self) -> None:
        html = render_timeline(_events(), show_scale=False)
        self.assertNotIn('<section class="scale-panel">', html)
        self.assertNotIn('<div class="axis">', html)

    def test_hide_scale_page_count(self) -> None:
        events = _events() + [Event(1956, "社会主义改造完成", "三大改造完成", "政治")]
        html = render_timeline(events, per_page=2, show_scale=False)
        self.assertEqual(html.count('<section class="page">'), 3)

    def test_scale_single_year(self) -> None:
        html = render_timeline([Event(1919, "五四运动")])
        self.assertIn('<span class="axis-dot"></span>', html)


class RenderCardTests(unittest.TestCase):
    def test_event_titles_rendered(self) -> None:
        html = render_timeline(_events())
        for event in _events():
            self.assertIn(event.title, html)

    def test_card_years_rendered(self) -> None:
        html = render_timeline(_events())
        self.assertIn('<div class="card-year">1919</div>', html)

    def test_description_escaped(self) -> None:
        html = render_timeline([Event(1919, "标题", "a & b <b>c</b>", "政治")])
        self.assertIn("a &amp; b &lt;b&gt;c&lt;/b&gt;", html)
        self.assertNotIn("<b>c</b>", html)

    def test_event_title_escaped(self) -> None:
        html = render_timeline([Event(1919, "<script>alert(1)</script>", "描述", "政治")])
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)
        self.assertNotIn("<script>alert(1)</script>", html)

    def test_category_tag_rendered(self) -> None:
        html = render_timeline(_events())
        self.assertIn('<span class="tag">政治</span>', html)
        self.assertIn('<span class="tag">战争</span>', html)

    def test_category_class_limited(self) -> None:
        events = [
            Event(1900 + index, "事件{}".format(index), "", "分类{}".format(index))
            for index in range(7)
        ]
        html = render_timeline(events)
        self.assertNotIn("cat-5", html)
        self.assertIn("cat-0", html)
        self.assertIn("cat-4", html)

    def test_no_category_no_tag(self) -> None:
        html = render_timeline([Event(1919, "无分类事件")])
        self.assertNotIn('<span class="tag">', html)

    def test_compact_layout_for_many_cards(self) -> None:
        html = render_timeline(_events(), per_page=12)
        self.assertIn("timeline cards compact", html)


class RenderPaginationTests(unittest.TestCase):
    def test_pagination_page_count(self) -> None:
        events = [
            Event(1900 + index, "事件{}".format(index), "描述", "分类")
            for index in range(7)
        ]
        html = render_timeline(events, per_page=3)
        self.assertEqual(html.count('<section class="page">'), 4)

    def test_page_numbering(self) -> None:
        events = [
            Event(1900 + index, "事件{}".format(index), "描述", "分类")
            for index in range(7)
        ]
        html = render_timeline(events, per_page=3)
        self.assertIn("第 1 / 4 页", html)
        self.assertIn("第 4 / 4 页", html)

    def test_invalid_per_page_zero(self) -> None:
        with self.assertRaises(TimelineError):
            render_timeline(_events(), per_page=0)

    def test_invalid_per_page_too_large(self) -> None:
        with self.assertRaises(TimelineError):
            render_timeline(_events(), per_page=31)


class RenderEmptyTests(unittest.TestCase):
    def test_empty_render(self) -> None:
        html = render_empty("空标题")
        self.assertIn("暂无符合条件的历史事件", html)
        self.assertIn("空标题", html)
        self.assertEqual(html.count('<section class="page">'), 1)
        self.assertIn("第 1 / 1 页", html)

    def test_render_timeline_empty(self) -> None:
        html = render_timeline([])
        self.assertIn("暂无符合条件的历史事件", html)
        self.assertEqual(html.count('<section class="page">'), 1)

    def test_invalid_title_type(self) -> None:
        with self.assertRaises(TimelineError):
            render_timeline(_events(), title=123)  # type: ignore[arg-type]

    def test_invalid_show_scale(self) -> None:
        with self.assertRaises(TimelineError):
            render_timeline(_events(), show_scale="yes")  # type: ignore[arg-type]

    def test_invalid_event_object(self) -> None:
        with self.assertRaises(TimelineError):
            render_timeline([{"year": 1919}])  # type: ignore[list-item]


if __name__ == "__main__":
    unittest.main()
