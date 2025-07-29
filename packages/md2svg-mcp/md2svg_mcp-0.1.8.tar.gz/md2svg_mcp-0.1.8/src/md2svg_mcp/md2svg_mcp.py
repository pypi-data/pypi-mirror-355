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


def calculate_text_width(text: str, font_size: int) -> int:
    # 分别处理中英文字符
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    english_chars = len(text) - chinese_chars
    # 中文字符宽度约为字体大小，英文字符宽度约为字体大小的0.6
    return int(chinese_chars * font_size + english_chars * font_size * 0.6)

def wrap_text(text: str, max_width: int, font_size: int, padding: int = 0) -> List[str]:
    # 考虑padding后的实际可用宽度
    available_width = max_width - (2 * padding)
    
    # 动态计算每行字符数
    result = []
    current_line = ""
    current_width = 0
    
    for char in text:
        # 计算当前字符宽度
        char_width = font_size if '\u4e00' <= char <= '\u9fff' else font_size * 0.6
        
        # 如果添加当前字符会导致超过可用宽度，开始新行
        if current_width + char_width > available_width:
            result.append(current_line)
            current_line = char
            current_width = char_width
        else:
            current_line += char
            current_width += char_width
    
    # 添加最后一行
    if current_line:
        result.append(current_line)
    
    return result

def draw_table(table_lines, x, y, width, font_family, font_size, text_color, header_color, border_color):
    svg = []
    rows = [re.findall(r"\|([^|]+)", line.strip()) for line in table_lines if '|' in line]
    if len(rows) < 2:
        return svg, y

    col_count = len(rows[0])
    col_width = max(80, (width - 2 * x) / col_count)
    row_height = int(font_size * 2.2)

    wrapped_rows = []
    max_lines_in_row = []
    
    for row in rows:
        wrapped_row = []
        max_lines = 1
        for col_idx, cell in enumerate(row):
            # 考虑单元格padding的实际可用宽度
            cell_padding = 16  # 单元格左右各8px的padding
            available_width = col_width - cell_padding
            wrapped_text = wrap_text(cell.strip(), available_width, font_size)
            wrapped_row.append(wrapped_text)
            max_lines = max(max_lines, len(wrapped_text))
        wrapped_rows.append(wrapped_row)
        max_lines_in_row.append(max_lines)

    total_height = sum(max_lines * row_height for max_lines in max_lines_in_row)

    svg.append(f'<rect x="{x-2}" y="{y-2}" width="{col_width*col_count + 4}" height="{total_height + 4}" fill="#fcfcfc" rx="8" ry="8" stroke="none"/>')

    current_y = y
    for row_idx, (wrapped_row, max_lines) in enumerate(zip(wrapped_rows, max_lines_in_row)):
        row_height_total = max_lines * row_height
        
        for col_idx, wrapped_cell in enumerate(wrapped_row):
            cx = x + col_idx * col_width
            
            if row_idx == 0:
                svg.append(f'<rect x="{cx}" y="{current_y}" width="{col_width}" height="{row_height_total}" fill="#e1f0fb" />')
                if col_idx == 0:
                    svg.append(f'<line x1="{x}" y1="{current_y + row_height_total}" x2="{x + col_width * col_count}" y2="{current_y + row_height_total}" stroke="{header_color}" stroke-width="2"/>')
            else:
                if row_idx % 2 == 1:
                    svg.append(f'<rect x="{cx}" y="{current_y}" width="{col_width}" height="{row_height_total}" fill="#fafafa" />')

            svg.append(f'<rect x="{cx}" y="{current_y}" width="{col_width}" height="{row_height_total}" fill="none" stroke="{border_color}" stroke-width="1"/>')

            align_x = cx + 8 if col_idx == 0 else cx + col_width / 2
            anchor = "start" if col_idx == 0 else "middle"
            fill = header_color if row_idx == 0 else text_color
            weight = "bold" if row_idx == 0 else "normal"

            for line_idx, line in enumerate(wrapped_cell):
                text_y = current_y + (line_idx + 0.5) * row_height
                svg.append(
                    f'<text x="{align_x}" y="{text_y}" font-size="{font_size}" font-family="{font_family}" '
                    f'fill="{fill}" font-weight="{weight}" text-anchor="{anchor}" dominant-baseline="middle">'
                    f'{escape(line)}</text>'
                )

        current_y += row_height_total

    return svg, current_y + 20


mcp = FastMCP(name="Md2svg-mcp")

@mcp.tool()
def markdown_to_svg(
    md_text: Annotated[str, "Markdown文本内容"],
    output_file_path: Annotated[str, "输出SVG文件路径"] = "output.svg",
    width: Annotated[int, "SVG图像宽度"] = 720,
    padding: Annotated[int, "SVG图像内边距"] = 50
) -> Annotated[str, "生成的SVG文件路径"]:
    """mardown转换为svg图片"""
    if isinstance(md_text, str):
        try:
            md_text.encode('utf-8')
        except UnicodeEncodeError:
            print("Warning: Input string is not valid UTF-8. Trying to decode with GBK...")
            md_text = md_text.encode('gbk', errors='ignore').decode('gbk', errors='ignore')
    
    blocks = parse_markdown(md_text)

    font_family = "Helvetica, sans-serif"
    line_height = 34
    font_size = 18
    y = padding
    svg_elements = []

    background_color = "#fefefe"
    code_bg_color = "#f0f0f0"
    code_text_color = "#2c3e50"
    text_color = "#2c3e50"
    h1_color = "#0277bd"
    h2_color = "#0288d1"
    bullet_color = "#4a4a4a"
    header_color = "#01579b"
    border_color = "#ddd"

    # 考虑padding后的实际可用宽度
    available_width = width - (2 * padding)

    for block_type, text in blocks:
        if block_type == "br":
            y += line_height // 2
            continue
        if not text and block_type != "code":
            continue

        if block_type == "h1":
            wrapped_lines = wrap_text(text, available_width, 32, padding)
            for line in wrapped_lines:
                svg_elements.append(
                    f'<text x="{padding}" y="{y}" font-size="32" font-weight="bold" fill="{h1_color}" '
                    f'font-family="{font_family}">{escape(line)}</text>'
                )
                y += int(line_height * 1.6)
        elif block_type == "h2":
            wrapped_lines = wrap_text(text, available_width, 24, padding)
            for line in wrapped_lines:
                svg_elements.append(
                    f'<text x="{padding}" y="{y}" font-size="24" font-weight="bold" fill="{h2_color}" '
                    f'font-family="{font_family}">{escape(line)}</text>'
                )
                y += int(line_height * 1.4)
        elif block_type == "code":
            code_lines = text.split("\n")
            # 代码块考虑padding和额外的留白
            code_padding = 14
            box_height = len(code_lines) * (line_height - 10) + 24
            svg_elements.append(
                f'<rect x="{padding-code_padding}" y="{y-code_padding}" '
                f'width="{available_width + 2*code_padding}" height="{box_height}" '
                f'fill="{code_bg_color}" rx="10" ry="10" />'
            )
            for i, line in enumerate(code_lines):
                svg_elements.append(
                    f'<text xml:space="preserve" x="{padding}" y="{y + i * (line_height - 10)}" '
                    f'font-size="16" fill="{code_text_color}" font-family="Courier New, monospace" '
                    f'dominant-baseline="hanging">{escape(line)}</text>'
                )
            y += box_height + 18
        elif block_type == "li":
            # 列表项需要考虑缩进和项目符号的空间
            indent = 28
            wrapped_lines = wrap_text(text, available_width - indent, font_size, padding)
            for i, line in enumerate(wrapped_lines):
                x_offset = padding + indent
                if i == 0:
                    svg_elements.append(f'<circle cx="{padding + 12}" cy="{y + 6}" r="5" fill="{bullet_color}" />')
                svg_elements.append(
                    f'<text x="{x_offset}" y="{y}" font-size="{font_size}" fill="{text_color}" '
                    f'font-family="{font_family}" dominant-baseline="hanging">{escape(line)}</text>'
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
        else:  # 普通段落
            wrapped_lines = wrap_text(text, available_width, font_size, padding)
            for line in wrapped_lines:
                svg_elements.append(
                    f'<text x="{padding}" y="{y}" font-size="{font_size}" fill="{text_color}" '
                    f'font-family="{font_family}" dominant-baseline="hanging">{escape(line)}</text>'
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
