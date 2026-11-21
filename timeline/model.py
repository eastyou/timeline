from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class Event:
    """一条历史事件记录。"""

    year: int
    title: str
    description: str = ""
    category: str = ""


class TimelineError(ValueError):
    """时间轴项目的自定义错误，用于提示可读的中文信息。"""


def _cell(row: Sequence[str], index: Optional[int]) -> str:
    """安全读取一行中的某一列，越界时返回空字符串。"""
    if index is None or index < 0 or index >= len(row):
        return ""
    return str(row[index]).strip()


def _parse_year(raw: str, line_no: int) -> int:
    """把 year 列转换为整数，非法时给出明确的行号与列名。"""
    if not raw:
        raise TimelineError("第 {} 行 year 列不能为空".format(line_no))
    try:
        return int(raw)
    except ValueError as exc:
        raise TimelineError(
            "第 {} 行 year 列必须是整数，实际值为 {!r}".format(line_no, raw)
        ) from exc


def parse_csv_text(text: str) -> List[Event]:
    """解析 CSV 文本并返回按年份、标题排序的事件列表。"""
    if not isinstance(text, str):
        raise TimelineError("CSV 内容必须是字符串")

    # 兼容直接读取到内存且带 BOM 的场景。
    if text.startswith("\ufeff"):
        text = text[1:]

    reader = csv.reader(io.StringIO(text), strict=True)
    rows: List[Tuple[int, List[str]]] = []
    try:
        for row in reader:
            line_no = reader.line_num
            if any(cell.strip() for cell in row):
                rows.append((line_no, list(row)))
    except csv.Error as exc:
        raise TimelineError(
            "CSV 格式错误（第 {} 行）：{}".format(reader.line_num, exc)
        ) from exc

    if not rows:
        raise TimelineError("CSV 内容为空，至少需要表头 year,title")

    header_line, header_row = rows[0]
    header = [cell.strip().lower() for cell in header_row]
    missing = [name for name in ("year", "title") if name not in header]
    if missing:
        raise TimelineError(
            "第 {} 行表头缺少必需列：{}（至少需要 year 与 title）".format(
                header_line, "、".join(missing)
            )
        )

    year_index = header.index("year")
    title_index = header.index("title")
    description_index = header.index("description") if "description" in header else None
    category_index = header.index("category") if "category" in header else None

    events: List[Event] = []
    for line_no, row in rows[1:]:
        year = _parse_year(_cell(row, year_index), line_no)
        title = _cell(row, title_index)
        if not title:
            raise TimelineError("第 {} 行 title 列不能为空".format(line_no))
        description = _cell(row, description_index)
        category = _cell(row, category_index)
        events.append(
            Event(
                year=year,
                title=title,
                description=description,
                category=category,
            )
        )

    events.sort(key=lambda event: (event.year, event.title))
    return events


def read_csv(path: Path) -> List[Event]:
    """读取 CSV 文件，依次尝试 UTF-8（含 BOM）与 GBK 编码。"""
    file_path = Path(path)
    try:
        raw = file_path.read_bytes()
    except FileNotFoundError as exc:
        raise FileNotFoundError("文件不存在：{}".format(file_path)) from exc
    except IsADirectoryError as exc:
        raise TimelineError("不是有效的 CSV 文件（目标是目录）：{}".format(file_path)) from exc
    except PermissionError as exc:
        raise PermissionError("没有读取权限：{}".format(file_path)) from exc
    except OSError as exc:
        raise OSError("读取文件失败：{}（{}）".format(file_path, exc)) from exc

    for encoding in ("utf-8-sig", "gbk"):
        try:
            text = raw.decode(encoding)
        except UnicodeDecodeError:
            continue
        return parse_csv_text(text)

    raise TimelineError(
        "无法解码文件 {}，请使用 UTF-8 或 GBK 编码".format(file_path)
    )


def filter_events(
    events: Sequence[Event],
    start: Optional[int] = None,
    end: Optional[int] = None,
    category: Optional[str] = None,
) -> List[Event]:
    """按年份闭区间与分类精确筛选事件。"""
    if start is not None and not isinstance(start, int):
        raise TimelineError("起始年份必须是整数")
    if end is not None and not isinstance(end, int):
        raise TimelineError("结束年份必须是整数")
    if start is not None and end is not None and start > end:
        raise TimelineError(
            "起始年份不能大于结束年份：{} > {}".format(start, end)
        )

    normalized_category = category.strip() if isinstance(category, str) else ""
    if category is not None and not isinstance(category, str):
        raise TimelineError("分类必须是文本")

    result: List[Event] = []
    for event in events:
        if start is not None and event.year < start:
            continue
        if end is not None and event.year > end:
            continue
        if normalized_category:
            if event.category.strip() != normalized_category:
                continue
        result.append(event)
    return result


def year_range(events: Sequence[Event]) -> Tuple[int, int]:
    """返回事件集合的年份范围（最小值、最大值）。"""
    if not events:
        raise TimelineError("没有可渲染的历史事件")
    years = [event.year for event in events]
    return min(years), max(years)


def position_ratio(year: int, start: int, end: int) -> float:
    """把年份映射为 0..1 的比例，用于年代尺定位。"""
    if not isinstance(year, int) or not isinstance(start, int) or not isinstance(end, int):
        raise TimelineError("年份参数必须是整数")
    if start > end:
        raise TimelineError(
            "起始年份不能大于结束年份：{} > {}".format(start, end)
        )
    if year < start or year > end:
        raise TimelineError(
            "年份 {} 超出范围 {}..{}".format(year, start, end)
        )
    if start == end:
        return 0.5
    ratio = (year - start) / float(end - start)
    # 浮点运算后做一次安全截断，保证始终处于 0..1。
    if ratio < 0.0:
        return 0.0
    if ratio > 1.0:
        return 1.0
    return ratio


def paginate(events: Sequence[Event], per_page: int) -> List[List[Event]]:
    """把事件按每页数量切分，per_page 限制在 1..30。"""
    if isinstance(per_page, bool) or not isinstance(per_page, int):
        raise TimelineError("每页事件数必须是整数")
    if per_page < 1 or per_page > 30:
        raise TimelineError(
            "每页事件数必须在 1 到 30 之间，实际为 {}".format(per_page)
        )
    if not events:
        return []
    return [list(events[index:index + per_page]) for index in range(0, len(events), per_page)]


def demo_events() -> List[Event]:
    """内置 12 条中国近现代史事件，供示例命令与测试使用。"""
    return [
        Event(1840, "鸦片战争", "英国发动侵华战争，中国近代史开端", "战争"),
        Event(1851, "太平天国运动", "洪秀全在广西金田起义", "政治"),
        Event(1894, "甲午中日战争", "黄海海战，北洋水师覆没", "战争"),
        Event(1898, "戊戌变法", "康有为、梁启超推动维新变法", "改革"),
        Event(1900, "义和团运动", "反帝爱国运动兴起", "社会"),
        Event(1911, "辛亥革命", "武昌起义推翻清朝统治", "政治"),
        Event(1919, "五四运动", "北京学生游行示威，新民主主义革命开端", "文化"),
        Event(1921, "中国共产党成立", "中共一大在上海召开", "政治"),
        Event(1931, "九一八事变", "日本侵占东北", "战争"),
        Event(1937, "七七事变", "全民族抗战爆发", "战争"),
        Event(1945, "抗日战争胜利", "日本宣布无条件投降", "战争"),
        Event(1949, "新中国成立", "中华人民共和国中央人民政府成立", "政治"),
    ]
