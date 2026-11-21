# timeline

[![CI](https://github.com/eastyou/timeline/actions/workflows/ci.yml/badge.svg)](https://github.com/eastyou/timeline/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)


把 CSV 历史事件整理成 **A4 可打印时间轴**：按年份排序、按年份比例定位、自动分页，并支持按年代与分类筛选。面向教师备课、学生作品集与课堂展示。

- Python 3.9+，仅使用标准库，零第三方依赖
- 输出单文件 HTML，浏览器直接打印为 A4
- 第一页为横向「年代尺」，之后每页为竖直事件卡片
- 所有文本自动 HTML 转义，分类使用有限的安全配色

## 安装

```bash
pip install -e .
```

也可以不安装，直接在仓库根目录运行：

```bash
python -m timeline --help
```

## CSV 格式

表头必需，列顺序可变，至少包含 `year` 与 `title`：

```csv
year,title,description,category
1919,五四运动,北京学生游行示威,政治
```

- `year`：整数年份，例如 `1919`
- `title`：事件标题，不能为空
- `description`：可选描述
- `category`：可选分类，用于图例与配色

文件编码支持 UTF-8（含 BOM）与 GBK。

## 使用

```bash
# 生成示例 CSV
timeline demo -o events.csv

# 生成完整时间轴
timeline -i events.csv -o timeline.html

# 按年代与分类筛选
timeline -i events.csv --start 1919 --end 1949 --category 战争 -o war.html

# 自定义标题与每页事件数
timeline -i events.csv --title "中国近现代史" --per-page 8 -o history.html
```

示例输出见 `examples/events.csv` 与 `examples/timeline.html`。

### 退出码

| 退出码 | 含义 |
| --- | --- |
| 0 | 成功 |
| 1 | 文件不存在、无权限或写入失败 |
| 2 | 参数非法、CSV 内容非法或筛选区间错误 |

## 开发与测试

```bash
python -m unittest discover -s tests -v
```

测试覆盖 CSV 解析、排序、筛选、年代尺比例、分页、HTML 转义、空状态与 CLI 退出码。

## 项目结构

```
timeline/
├── timeline/
│   ├── model.py      # Event、CSV 解析、筛选、分页
│   ├── render.py     # A4 HTML 渲染
│   ├── cli.py        # 命令行入口
│   └── __main__.py
├── tests/
├── examples/
└── pyproject.toml
```

## 许可

MIT License，Copyright (c) 2026 eastyou。
