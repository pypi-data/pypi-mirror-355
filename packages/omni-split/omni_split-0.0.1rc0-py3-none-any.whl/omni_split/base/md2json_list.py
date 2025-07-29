from mistletoe import Document
from mistletoe.block_token import Heading, Paragraph, BlockCode, List, ListItem, Quote, Table, TableRow, TableCell, ThematicBreak, CodeFence
from mistletoe.span_token import Strong, Emphasis, Link, Image, RawText
import json
import re

# #     {
#         "type": "text",
#         "text": "Game-theoretic Workflow in this Paper  In this paper, we integrate game-theoretic principles into. the reasoning processes of LLMs prior to decision-making. By guiding the models to derive rational. strategies and make decisions based on these strategies, we aim to enhance their ability to perform effectively in strategic settings. ",
#         "page_idx": 4
#     },
# {
#     "type": "text",
#     "text": "Game-theoretic LLM: Agent Workflow for Negotiation Games ",
#     "text_level": 1,
#     "page_idx": 0
# },
# {
#     "type": "image",
#     "img_path": "images/9d516d401a6bdc168c3000baaf9f12a86aac5e2b07edb16344678c15119aebb1.jpg",
#     "img_caption": [
#         "Figure 1: Game-theoretic Landscape Investigated in this Paper. "
#     ],
#     "img_footnote": [],
#     "page_idx": 3
# },
# {
#     "type": "table",
#     "img_path": "images/f20e0b1b16500e94a492a40b553e7e3ae8ffe66d69de3c9252ee11b32982775b.jpg",
#     "table_caption": [
#         "Table 3b: Payoff matrix for Wait-Go Game "
#     ],
#     "table_footnote": [],
#     "table_body": "\n\n<html><body><table><tr><td></td><td>Wait</td><td>Go</td></tr><tr><td>Wait</td><td>0,0</td><td>0, 2</td></tr><tr><td>Go</td><td>2,0</td><td>-4,-4</td></tr></table></body></html>\n\n",
#     "page_idx": 7
# },


def is_markdown_equal(md_str):
    md_str = md_str.strip()  # 去除前后空白
    # 检查是否以 $$ 开头和结尾，并且中间没有 $$
    return bool(re.fullmatch(r"^\$\$(.*?)\$\$", md_str, re.DOTALL))


def is_markdown_table(md_str):
    md_str = md_str.strip()
    if md_str.startswith("<html><body><table>") and md_str.endswith("</table></body></html>"):
        return True
    lines = [line.strip() for line in md_str.split("\n") if line.strip()]
    if not lines:
        return False

    # 检查所有行是否至少包含一个普通 |（非转义）
    for line in lines:
        if "|" not in line:
            return False

    # 单行内容不视为表格（除非是严格的单行表格，但通常 Markdown 表格需要分隔线）
    if len(lines) == 1:
        return False  # 直接返回 False，避免误判 LaTeX 等

    # 多行表格：检查第二行是否是分隔线
    separator_line = lines[1]
    separator_parts = [part.strip() for part in separator_line.split("|") if part.strip()]
    for part in separator_parts:
        if not re.fullmatch(r"^:?-+:?$", part):
            return False

    return True  # 只有符合所有条件才返回 True


def split_image_url_func(text):
    parts = re.split(r"(!\[\]\([^)]+\))", text.strip('"'))
    parts = [p for p in parts if p]
    ret_parts = []
    for item in parts:
        if item != "":
            ret_parts.append(item)
    return ret_parts


def md2json_list_func(md_content):
    # 解析Markdown为AST
    doc = Document(md_content)

    result = []

    # 遍历AST中的每个节点
    for child in doc.children:
        # 处理标题
        if isinstance(child, Heading):
            level = child.level
            content = get_inline_md(child.children) if hasattr(child, "children") and child.children else ""
            result.append({"text": content, "type": "text", "text_level": level, "page_idx": None})

        # 处理段落
        elif isinstance(child, Paragraph):
            # 检查是否是独立的图片
            ## todo
            if hasattr(child, "children") and child.children and len(child.children) == 1 and isinstance(child.children[0], Image):
                img = child.children[0]
                result.append(
                    {
                        "type": "image",
                        "img_path": img.src,
                        "img_caption": [img.title if hasattr(img, "title") else ""],
                        "img_footnote": [img.title if hasattr(img, "title") else ""],
                        "page_idx": None,
                    },
                )
                # result.append({"content": {"src": img.src if hasattr(img, "src") else "", "title": img.title if hasattr(img, "title") else "", "description": img.title if hasattr(img, "title") else ""}, "type": "image"})
            else:
                content = get_inline_md(child.children) if hasattr(child, "children") and child.children else ""
                split_content_list = split_image_url_func(content)
                for split_content in split_content_list:
                    if split_content.startswith("![") and split_content.endswith(")"):
                        ##note: 处理图片
                        temp = {
                            "type": "image",
                            "img_path": split_content[4:-1],
                            "img_caption": [""],
                            "img_footnote": [""],
                            "page_idx": None,
                        }

                    elif is_markdown_table(split_content):
                        ##note:  处理表格
                        ## 处理表格
                        temp = {
                            "type": "table",
                            "img_path": None,
                            "table_caption": [""],
                            "table_footnote": [""],
                            "table_body": f"{split_content}\n",
                            "page_idx": None,
                        }

                    elif is_markdown_equal(split_content):
                        ##note:  处理单行公式(非行内公式)
                        temp = {
                            "type": "equation",
                            "text": f"{split_content}\n",
                            "text_format": "latex",
                            "page_idx": None,
                        }

                    else:
                        ##note: 其他的按照标准text对待.
                        temp = {
                            "text": f"{split_content}\n",
                            "type": "text",
                            "page_idx": None,
                        }

                    result.append(temp)
        # 处理代码块
        elif isinstance(child, (BlockCode, CodeFence)):
            if isinstance(child, BlockCode):
                # BlockCode（缩进代码块）：手动添加 ``` 标记
                code_content = child.children[0].content if hasattr(child, "children") and child.children else ""
                language = ""
                code_content = f"```\n{code_content}\n```"  # 添加 ``` 围栏
            else:
                # CodeFence（围栏代码块）：保留原始 ```language\ncontent\n```
                code_content = child.children[0].content if hasattr(child, "children") and child.children else ""
                language = getattr(child, "language", "")

                fence_char = getattr(child, "fence_char", "`")  # 可能是 ` 或 ~
                fence_length = getattr(child, "fence_length", 3)  # 通常是 3
                fence = fence_char * fence_length

                code_content = f"{fence}{language}\n{code_content}\n{fence}"

            result.append({"content": code_content, "type": "code", "language": language})

        # 处理列表
        elif isinstance(child, List):
            items = []
            if hasattr(child, "children") and child.children:
                for item in child.children:
                    if isinstance(item, ListItem):
                        item_content = get_inline_md(item.children) if hasattr(item, "children") and item.children else ""
                        items.append(item_content)

            # result.append({"content": items, "type": "list", "ordered": child.start is not None if hasattr(child, "start") else False})
            temp_str = ""
            for item in items:
                temp_str += "- " + item + "\n"
            temp = {
                "text": temp_str,
                "type": "text",
                "page_idx": None,
            }
            result.append(temp)

        # 处理引用
        elif isinstance(child, Quote):
            content = get_inline_md(child.children) if hasattr(child, "children") and child.children else ""
            temp = {
                "text": str(content)+"\n",
                "type": "text",
                "page_idx": None,
            }
            result.append(temp)

            # result.append({"content": content, "type": "text", "page_idx": None})

        # 处理表格
        elif isinstance(child, Table):
            table_content = ""
            if hasattr(child, "children") and child.children:
                # 重建表格的Markdown表示
                if hasattr(child, "header") and child.header:
                    header_row = child.header
                    if hasattr(header_row, "children") and header_row.children:
                        table_content += "| " + " | ".join(get_inline_md(cell.children) if hasattr(cell, "children") else "" for cell in header_row.children if isinstance(cell, TableCell)) + " |\n"
                        table_content += "| " + " | ".join(["---"] * len(header_row.children)) + " |\n"

                for row in child.children[1:] if hasattr(child, "children") else []:
                    if isinstance(row, TableRow) and hasattr(row, "children") and row.children:
                        table_content += "| " + " | ".join(get_inline_md(cell.children) if hasattr(cell, "children") else "" for cell in row.children if isinstance(cell, TableCell)) + " |\n"
            result.append(
                {
                    "type": "table",
                    "img_path": None,
                    "table_caption": [""],
                    "table_footnote": [""],
                    "table_body": table_content.strip(),
                    "page_idx": None,
                }
            )
        # 处理分隔线
        elif isinstance(child, ThematicBreak):
            result.append(
                {
                    "content": "---\n",
                    "type": "text",
                    "page_idx": None,
                }
            )
        # 处理数学公式块
        elif is_math_block(child):
            content = child.children[0].content.strip() if hasattr(child, "children") and child.children and len(child.children) > 0 else ""
            result.append(
                {
                    "type": "equation",
                    "text": content,
                    "text_format": "latex",
                    "page_idx": None,
                }
            )

    return result


def get_inline_md(tokens):
    """获取行内元素的Markdown表示"""
    if not tokens:
        return ""

    md = ""
    for token in tokens:
        if isinstance(token, RawText):
            md += token.content if hasattr(token, "content") else ""
        elif isinstance(token, Strong):
            md += f"**{get_inline_md(token.children) if hasattr(token, 'children') else ''}**"
        elif isinstance(token, Emphasis):
            md += f"*{get_inline_md(token.children) if hasattr(token, 'children') else ''}*"
        elif isinstance(token, Link):
            md += f"[{get_inline_md(token.children) if hasattr(token, 'children') else ''}]({token.target if hasattr(token, 'target') else ''})"
        elif isinstance(token, Image):
            md += f"![{token.title if hasattr(token, 'title') else ''}]({token.src if hasattr(token, 'src') else ''})"
        elif is_math_inline(token):
            content = token.children[0].content if hasattr(token, "children") and token.children and len(token.children) > 0 else ""
            md += f"${content}$"
        elif hasattr(token, "children"):
            md += get_inline_md(token.children) if token.children else ""
    return md


def is_math_block(token):
    """检查是否是数学公式块"""
    if isinstance(token, Paragraph) and hasattr(token, "children") and token.children and len(token.children) == 1:
        content = token.children[0].content.strip() if hasattr(token.children[0], "content") else ""
        return isinstance(token.children[0], RawText) and content.startswith("$$") and content.endswith("$$")
    return False


def is_math_inline(token):
    """检查是否是行内数学公式"""
    if isinstance(token, RawText):
        content = token.content.strip() if hasattr(token, "content") else ""
        return content.startswith("$") and content.endswith("$") and len(content) > 1
    return False


if __name__ == "__main__":
    print("main function invoke")
    with open("./test/c8d4614affc19ba92d7ba0671fd709803d0488a0c5a68bc237783a8af39fe32e/1c7fbb26-1012-4b03-894c-69ab2257985c_1743677710.4311144.md", "r") as f:
        md_content = f.read()

    json_list = md2json_list_func(md_content)
    print(json.dumps(json_list, indent=4, ensure_ascii=False))
