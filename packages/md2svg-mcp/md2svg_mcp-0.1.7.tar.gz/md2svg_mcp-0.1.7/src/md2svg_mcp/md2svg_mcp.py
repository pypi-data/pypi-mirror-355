# -*- coding: utf-8 -*-
import textwrap
from xml.sax.saxutils import escape
import re
from fastmcp import FastMCP
from typing import Annotated, List, Tuple


def parse_markdown(md_text):
    lines = md_text.split('\n')
    blocks = []
    in_code = False
    code_lines = []
    in_table = False
    table_lines = []

    for line in lines:
        if line.strip().startswith("```"):
            if in_code:
                blocks.append(("code", "\n".join(code_lines)))
                code_lines = []
            in_code = not in_code
            continue

        if in_code:
            code_lines.append(line)
            continue

        if re.match(r"^\|.*\|.*$", line):
            table_lines.append(line)
            in_table = True
            continue
        elif in_table and line.strip() == "":
            blocks.append(("table", table_lines))
            table_lines = []
            in_table = False
            continue
        elif in_table:
            table_lines.append(line)
            continue

        if line.startswith("# "):
            blocks.append(("h1", line[2:].strip()))
        elif line.startswith("## "):
            blocks.append(("h2", line[3:].strip()))
        elif line.startswith("- ") or line.startswith("* "):
            blocks.append(("li", line[2:].strip()))
        elif line.strip() == "":
            blocks.append(("br", ""))
        else:
            blocks.append(("p", line.strip()))

    if code_lines:
        blocks.append(("code", "\n".join(code_lines)))
    if table_lines:
        blocks.append(("table", table_lines))

    return blocks


def draw_table(table_lines, x, y, width, font_family, font_size, text_color, header_color, border_color):
    svg = []
    # 过滤表格行内容
    rows = [re.findall(r"\|([^|]+)", line.strip()) for line in table_lines if '|' in line]
    if len(rows) < 2:
        return svg, y

    col_count = len(rows[0])
    # 减去两边padding后均分列宽，最大保持最小宽度限制
    col_width = max(80, (width - 2 * x) / col_count)
    row_height = int(font_size * 2.2)  # 高度适当加大

    table_height = row_height * len(rows)

    # 表格整体背景
    svg.append(f'<rect x="{x-2}" y="{y-2}" width="{col_width*col_count + 4}" height="{table_height + 4}" fill="#fcfcfc" rx="8" ry="8" stroke="none"/>')

    for row_idx, row in enumerate(rows):
        for col_idx, cell in enumerate(row):
            cx = x + col_idx * col_width
            cy = y + row_idx * row_height

            # 表头行背景色淡蓝
            if row_idx == 0:
                svg.append(f'<rect x="{cx}" y="{cy}" width="{col_width}" height="{row_height}" fill="#e1f0fb" />')
                # 表头底部加粗线条
                if col_idx == 0:
                    svg.append(f'<line x1="{x}" y1="{cy + row_height}" x2="{x + col_width * col_count}" y2="{cy + row_height}" stroke="{header_color}" stroke-width="2"/>')
            else:
                # 隔行浅灰
                if row_idx % 2 == 1:
                    svg.append(f'<rect x="{cx}" y="{cy}" width="{col_width}" height="{row_height}" fill="#fafafa" />')

            # 单元格边框
            svg.append(f'<rect x="{cx}" y="{cy}" width="{col_width}" height="{row_height}" fill="none" stroke="{border_color}" stroke-width="1"/>')

            # 内容对齐：首列左对齐，其他列居中
            align_x = cx + 8 if col_idx == 0 else cx + col_width / 2
            anchor = "start" if col_idx == 0 else "middle"
            fill = header_color if row_idx == 0 else text_color
            weight = "bold" if row_idx == 0 else "normal"

            # 文字垂直居中 y + 字体大小/3 调整基线
            text_y = cy + (row_height // 2) + (font_size // 3)

            svg.append(
                f'<text x="{align_x}" y="{text_y}" font-size="{font_size}" font-family="{font_family}" fill="{fill}" font-weight="{weight}" text-anchor="{anchor}" dominant-baseline="middle">'
                f'{escape(cell.strip())}</text>'
            )

    return svg, y + table_height + 20


mcp = FastMCP(name="Md2svg-mcp")

@mcp.tool()
def markdown_to_svg(
    md_text: Annotated[str, "Markdown文本内容"],
    output_file_path: Annotated[str, "输出SVG文件路径"] = "output.svg",
    width: Annotated[int, "SVG图像宽度"] = 720,
    padding: Annotated[int, "SVG图像内边距"] = 50
) -> Annotated[str, "生成的SVG文件路径"]:
    """mardown转换为svg图片"""
    # 如果需要，尝试将输入字符串解码为UTF-8（处理可能的GBK编码字符串）
    if isinstance(md_text, str):
        try:
            md_text.encode('utf-8')
        except UnicodeEncodeError:
            print("Warning: Input string is not valid UTF-8. Trying to decode with GBK...")
            # 如果字符串包含无法用UTF-8编码表示的字符，尝试用GBK解码再重新编码为UTF-8
            md_text = md_text.encode('gbk', errors='ignore').decode('gbk', errors='ignore')
    
    blocks = parse_markdown(md_text)

    font_family = "Helvetica, sans-serif"
    line_height = 34
    font_size = 18
    y = padding
    svg_elements = []

    # 清新配色
    background_color = "#fefefe"
    code_bg_color = "#f0f0f0"
    code_text_color = "#2c3e50"
    text_color = "#2c3e50"
    h1_color = "#0277bd"
    h2_color = "#0288d1"
    bullet_color = "#4a4a4a"
    header_color = "#01579b"
    border_color = "#ddd"

    for block_type, text in blocks:
        if block_type == "br":
            y += line_height // 2
            continue
        if not text and block_type != "code":
            continue

        if block_type == "h1":
            svg_elements.append(
                f'<text x="{padding}" y="{y}" font-size="32" font-weight="bold" fill="{h1_color}" font-family="{font_family}">{escape(text)}</text>'
            )
            y += int(line_height * 1.6)
        elif block_type == "h2":
            svg_elements.append(
                f'<text x="{padding}" y="{y}" font-size="24" font-weight="bold" fill="{h2_color}" font-family="{font_family}">{escape(text)}</text>'
            )
            y += int(line_height * 1.4)
        elif block_type == "code":
            code_lines = text.split("\n")
            box_height = len(code_lines) * (line_height - 10) + 24
            svg_elements.append(
                f'<rect x="{padding-14}" y="{y-14}" width="{width - 2 * padding + 28}" height="{box_height}" fill="{code_bg_color}" rx="10" ry="10" />'
            )
            # 代码字体行间距更紧凑
            for i, line in enumerate(code_lines):
                svg_elements.append(
                    f'<text xml:space="preserve" x="{padding}" y="{y + i * (line_height - 10)}" '
                    f'font-size="16" fill="{code_text_color}" font-family="Courier New, monospace" dominant-baseline="hanging">{escape(line)}</text>'
                )
            y += box_height + 18
        elif block_type == "li":
            wrapped_lines = textwrap.wrap(text, width=60)
            for i, line in enumerate(wrapped_lines):
                x_offset = padding + 28
                if i == 0:
                    svg_elements.append(f'<circle cx="{padding + 12}" cy="{y + 6}" r="5" fill="{bullet_color}" />')
                svg_elements.append(
                    f'<text x="{x_offset}" y="{y}" font-size="{font_size}" fill="{text_color}" font-family="{font_family}" dominant-baseline="hanging">{escape(line)}</text>'
                )
                y += line_height
            y += 4
        elif block_type == "table":
            table_svg, y = draw_table(
                table_lines=text,
                x=padding,
                y=y,
                width=width,
                font_family=font_family,
                font_size=font_size,
                text_color=text_color,
                header_color=header_color,
                border_color=border_color
            )
            svg_elements.extend(table_svg)
        else:
            wrapped_lines = textwrap.wrap(text, width=65)
            for line in wrapped_lines:
                svg_elements.append(
                    f'<text x="{padding}" y="{y}" font-size="{font_size}" fill="{text_color}" font-family="{font_family}" dominant-baseline="hanging">{escape(line)}</text>'
                )
                y += line_height
            y += 10

    height = y + padding
    svg_body = "\n".join(svg_elements)

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <style>
    text {{ user-select: none; }}
  </style>
  <rect width="100%" height="100%" fill="{background_color}"/>
  {svg_body}
</svg>'''

    with open(output_file_path, "w", encoding="utf-8") as f:
        f.write(svg)

    print(f"SVG 文件生成成功: {output_file_path}")


def main():
    mcp.run()


if __name__ == "__main__":
    main()
