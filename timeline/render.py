from __future__ import annotations

import html
from typing import Dict, List, Sequence

from .model import Event, TimelineError, paginate, position_ratio, year_range


_DEFAULT_TITLE = "历史事件时间轴"
_CATEGORY_COLORS = ("#b91c1c", "#1d4ed8", "#047857", "#b45309", "#6d28d9")

_CSS = """
@page { size: A4; margin: 0; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  background: #e2e8f0;
  color: #1e293b;
  font-family: "Noto Serif CJK SC", "Source Han Serif SC", "Songti SC", "SimSun", serif;
  font-size: 10pt;
  line-height: 1.55;
}
.page {
  width: 210mm;
  min-height: 297mm;
  padding: 12mm;
  box-sizing: border-box;
  overflow: hidden;
  background: #ffffff;
  margin: 0 auto 8mm;
  position: relative;
}
.page-inner {
  width: 98%;
  min-height: calc(297mm - 24mm);
  margin: 0 auto;
  display: flex;
  flex-direction: column;
}
@media print {
  body { background: #ffffff; }
  .page { margin: 0; page-break-after: always; break-after: page; }
  .page:last-child { page-break-after: auto; break-after: auto; }
}
.page-head {
  border-bottom: 0.7mm solid #0f172a;
  padding-bottom: 4mm;
  margin-bottom: 6mm;
}
.eyebrow {
  margin: 0 0 2mm;
  font-family: "Helvetica Neue", Arial, sans-serif;
  font-size: 8pt;
  letter-spacing: 0.35em;
  color: #64748b;
}
h1 { margin: 0; font-size: 26pt; letter-spacing: 0.06em; }
.subtitle { margin: 2mm 0 0; font-size: 10pt; color: #475569; }
.section-title { margin: 0 0 2mm; font-size: 12pt; }
.scale-panel { width: 100%; margin: 2mm 0 4mm; }
.axis { position: relative; height: 62mm; margin: 8mm 0 2mm; }
.axis-line {
  position: absolute;
  left: 0;
  right: 0;
  top: 50%;
  height: 0.7mm;
  background: #0f172a;
  border-radius: 0.35mm;
}
.axis-year {
  position: absolute;
  top: calc(50% + 4mm);
  transform: translateX(-50%);
  font-family: "Helvetica Neue", Arial, sans-serif;
  font-weight: 700;
  font-size: 9pt;
  color: #334155;
}
.axis-year.axis-end { top: auto; bottom: calc(50% + 4mm); }
.axis-event { position: absolute; top: 50%; width: 0; height: 0; }
.axis-dot {
  position: absolute;
  left: -1.5mm;
  top: -1.5mm;
  width: 3mm;
  height: 3mm;
  border-radius: 50%;
  background: var(--accent, #475569);
  border: 0.35mm solid #ffffff;
  box-shadow: 0 0 0 0.25mm var(--accent, #475569);
}
.axis-label {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  width: 16mm;
  text-align: center;
  font-family: "Helvetica Neue", Arial, sans-serif;
  font-size: 8pt;
  font-weight: 700;
  color: #334155;
}
.axis-event.top .axis-label { bottom: 4mm; }
.axis-event.bottom .axis-label { top: 4mm; }
.legend {
  list-style: none;
  display: flex;
  flex-wrap: wrap;
  gap: 3mm 6mm;
  margin: 6mm 0 0;
  padding: 5mm 6mm;
  background: #f8fafc;
  border-left: 1mm solid #0f172a;
}
.legend li { display: flex; align-items: center; font-size: 9pt; color: #334155; }
.legend-dot {
  width: 2.6mm;
  height: 2.6mm;
  border-radius: 50%;
  margin-right: 2mm;
  background: var(--accent, #64748b);
}
.timeline {
  position: relative;
  width: 100%;
  padding-left: 12mm;
  margin-top: 2mm;
}
.timeline::before {
  content: "";
  position: absolute;
  left: 3mm;
  top: 0;
  bottom: 0;
  width: 0.7mm;
  background: #cbd5e1;
}
.cards { flex: 1; }
.card {
  position: relative;
  padding: 3.5mm 4.5mm;
  margin: 0 0 6mm 0;
  background: #f8fafc;
  border-left: 1mm solid var(--accent, #64748b);
  border-radius: 0 2mm 2mm 0;
}
.card::before {
  content: "";
  position: absolute;
  left: -10.5mm;
  top: 6mm;
  width: 3mm;
  height: 3mm;
  border-radius: 50%;
  background: var(--accent, #64748b);
  border: 0.4mm solid #ffffff;
  box-shadow: 0 0 0 0.25mm var(--accent, #64748b);
}
.card-year {
  font-family: "Helvetica Neue", Arial, sans-serif;
  font-size: 12pt;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: var(--accent, #334155);
}
.card-title { margin: 1mm 0 1.5mm; font-size: 15pt; }
.tag {
  display: inline-block;
  padding: 0.6mm 2.5mm;
  border-radius: 4mm;
  font-family: "Helvetica Neue", Arial, sans-serif;
  font-size: 8pt;
  color: #ffffff;
  background: var(--accent, #64748b);
}
.card-desc { margin: 2mm 0 0; font-size: 10pt; color: #475569; }
.timeline.compact .card { padding: 2mm 3mm; margin-bottom: 3mm; }
.timeline.compact .card::before { top: 4mm; }
.timeline.compact .card-year { font-size: 10pt; }
.timeline.compact .card-title { margin: 0.5mm 0 1mm; font-size: 12pt; }
.timeline.compact .card-desc { margin-top: 1mm; font-size: 9pt; }
.compact-head { margin-bottom: 4mm; }
.compact-head h2 { margin: 0; font-size: 14pt; }
.compact-head .subtitle { font-size: 9pt; }
.page-footer {
  margin-top: auto;
  padding-top: 4mm;
  border-top: 0.3mm solid #cbd5e1;
  display: flex;
  justify-content: space-between;
  font-family: "Helvetica Neue", Arial, sans-serif;
  font-size: 8pt;
  color: #64748b;
}
.empty-head { border-bottom-color: #94a3b8; }
.empty-box {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 0.5mm dashed #cbd5e1;
  border-radius: 3mm;
  color: #64748b;
  font-size: 12pt;
}
.cat-0 { --accent: #b91c1c; }
.cat-1 { --accent: #1d4ed8; }
.cat-2 { --accent: #047857; }
.cat-3 { --accent: #b45309; }
.cat-4 { --accent: #6d28d9; }
.cat-none { --accent: #64748b; }
""".strip()


def _normalize_title(title: object) -> str:
    """校验并规范化页面标题，返回经过 HTML 转义的文本。"""
    if not isinstance(title, str):
        raise TimelineError("标题必须是文本")
    cleaned = title.strip() or _DEFAULT_TITLE
    return html.escape(cleaned, quote=True)


def _category_class_map(events: Sequence[Event]) -> Dict[str, str]:
    """为每个分类分配有限数量的 CSS 类，保证全文档配色一致。"""
    names = sorted({event.category.strip() for event in events if event.category.strip()})
    return {
        name: "cat-{}".format(index % len(_CATEGORY_COLORS))
        for index, name in enumerate(names)
    }


def _event_class(event: Event, class_map: Dict[str, str]) -> str:
    """返回事件对应的分类 CSS 类。"""
    return class_map.get(event.category.strip(), "cat-none")


def _render_scale(events: Sequence[Event], class_map: Dict[str, str]) -> str:
    """渲染第一页顶部的横向年代尺。"""
    start, end = year_range(events)
    parts: List[str] = [
        '<section class="scale-panel">',
        '<h2 class="section-title">年代尺</h2>',
        '<div class="axis">',
        '<div class="axis-line"></div>',
        '<span class="axis-year" style="left:0%">{}</span>'.format(start),
        '<span class="axis-year axis-end" style="left:100%">{}</span>'.format(end),
    ]
    for index, event in enumerate(events):
        ratio = position_ratio(event.year, start, end)
        side = "top" if index % 2 == 0 else "bottom"
        parts.append(
            '<div class="axis-event {side} {cls}" style="left:{left:.3f}%" '
            'title="{tip}">'
            '<span class="axis-dot"></span>'
            '<span class="axis-label">{year}</span>'
            "</div>".format(
                side=side,
                cls=_event_class(event, class_map),
                left=ratio * 100.0,
                tip=html.escape(event.title, quote=True),
                year=event.year,
            )
        )
    parts.append("</div>")
    parts.append(
        '<p class="subtitle">共 {} 个事件 · 按年份比例定位</p>'.format(len(events))
    )
    parts.append("</section>")
    return "\n".join(parts)


def _render_legend(events: Sequence[Event], class_map: Dict[str, str]) -> str:
    """渲染分类图例；无分类时返回空字符串。"""
    categories = sorted(
        {event.category.strip() for event in events if event.category.strip()}
    )
    if not categories:
        return ""
    items: List[str] = []
    for name in categories:
        items.append(
            '<li class="{cls}"><span class="legend-dot"></span>{name}</li>'.format(
                cls=class_map[name], name=html.escape(name, quote=True)
            )
        )
    return '<ul class="legend">\n{}\n</ul>'.format("\n".join(items))


def _render_card(event: Event, class_map: Dict[str, str]) -> str:
    """渲染单个事件卡片，所有外部文本均做 HTML 转义。"""
    parts: List[str] = [
        '<article class="card {}">'.format(_event_class(event, class_map)),
        '<div class="card-year">{}</div>'.format(event.year),
        '<h3 class="card-title">{}</h3>'.format(
            html.escape(event.title, quote=True)
        ),
    ]
    category = event.category.strip()
    if category:
        parts.append(
            '<span class="tag">{}</span>'.format(html.escape(category, quote=True))
        )
    if event.description:
        escaped = html.escape(event.description, quote=True).replace("\n", "<br>")
        parts.append('<p class="card-desc">{}</p>'.format(escaped))
    parts.append("</article>")
    return "\n".join(parts)


def _render_page(
    content: str, running_title: str, page_no: int, total: int
) -> str:
    """把内容包进一页 A4 容器并加上页脚。"""
    footer = (
        '<footer class="page-footer">'
        "<span>{}</span>"
        "<span>第 {} / {} 页</span>"
        "</footer>"
    ).format(running_title, page_no, total)
    return (
        '<section class="page">'
        '<div class="page-inner">'
        "{}\n{}"
        "</div>"
        "</section>"
    ).format(content, footer)


def _render_scale_page(
    events: Sequence[Event],
    title: str,
    start: int,
    end: int,
    class_map: Dict[str, str],
    page_no: int,
    total: int,
) -> str:
    """渲染包含标题、年代尺与图例的首页。"""
    content = "\n".join(
        [
            '<header class="page-head">',
            '<p class="eyebrow">TIMELINE</p>',
            "<h1>{}</h1>".format(title),
            '<p class="subtitle">{} — {} · 共 {} 个事件</p>'.format(
                start, end, len(events)
            ),
            "</header>",
            _render_scale(events, class_map),
            _render_legend(events, class_map),
        ]
    )
    return _render_page(content, title, page_no, total)


def _render_cards_page(
    page_events: Sequence[Event],
    title: str,
    start: int,
    end: int,
    class_map: Dict[str, str],
    page_no: int,
    total: int,
    per_page: int,
) -> str:
    """渲染一页竖直时间轴卡片。"""
    compact = " compact" if per_page > 10 else ""
    cards = "\n".join(_render_card(event, class_map) for event in page_events)
    content = "\n".join(
        [
            '<header class="page-head compact-head">',
            "<h2>{}</h2>".format(title),
            '<p class="subtitle">{} — {}</p>'.format(start, end),
            "</header>",
            '<div class="timeline cards{}">'.format(compact),
            cards,
            "</div>",
        ]
    )
    return _render_page(content, title, page_no, total)


def _document(title: str, body: str) -> str:
    """拼装完整的 HTML 文档。"""
    return (
        "<!DOCTYPE html>\n"
        '<html lang="zh-CN">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>{}</title>\n"
        "<style>\n{}\n</style>\n"
        "</head>\n"
        "<body>\n{}\n</body>\n"
        "</html>\n"
    ).format(title, _CSS, body)


def render_timeline(
    events: Sequence[Event],
    title: str = _DEFAULT_TITLE,
    per_page: int = 6,
    show_scale: bool = True,
) -> str:
    """把事件渲染为可打印的 A4 时间轴 HTML。"""
    if events is None:
        raise TimelineError("事件列表不能为空值")
    if not isinstance(show_scale, bool):
        raise TimelineError("show_scale 必须是布尔值")

    event_list = list(events)
    safe_title = _normalize_title(title)
    if not event_list:
        return render_empty(title)

    for event in event_list:
        if not isinstance(event, Event):
            raise TimelineError("事件数据必须是 Event 对象")

    event_list.sort(key=lambda item: (item.year, item.title))
    pages = paginate(event_list, per_page)
    class_map = _category_class_map(event_list)
    start, end = year_range(event_list)
    total_pages = len(pages) + (1 if show_scale else 0)

    blocks: List[str] = []
    page_no = 1
    if show_scale:
        blocks.append(
            _render_scale_page(
                event_list, safe_title, start, end, class_map, page_no, total_pages
            )
        )
        page_no += 1
    for page_events in pages:
        blocks.append(
            _render_cards_page(
                page_events,
                safe_title,
                start,
                end,
                class_map,
                page_no,
                total_pages,
                per_page,
            )
        )
        page_no += 1

    return _document(safe_title, "\n".join(blocks))


def render_empty(title: str = _DEFAULT_TITLE) -> str:
    """渲染没有事件时的提示页。"""
    safe_title = _normalize_title(title)
    content = "\n".join(
        [
            '<header class="page-head empty-head">',
            '<p class="eyebrow">TIMELINE</p>',
            "<h1>{}</h1>".format(safe_title),
            '<p class="subtitle">暂无符合条件的历史事件</p>',
            "</header>",
            '<div class="empty-box">',
            "<p>请在 CSV 中添加事件，或调整年份与分类筛选条件。</p>",
            "</div>",
        ]
    )
    return _document(safe_title, _render_page(content, safe_title, 1, 1))
