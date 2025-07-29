import json
import re

# 设置文本长度限制

# 定义假性公式的标志


# 定义占位符前缀
element_placeholder = {"equation": "[EQUATION]", "image": "[IMAGE]", "table": "[TABLE]"}
PSEUDO_EQUATION_FLAG = "[PSEUDO_EQUATION]"

# 用于保存占位符映射内容，格式：(placeholder, element_type, content)


# ---- 核心功能函数 ----
def count_words(text):
    """更精确的字数统计方法（接近Word统计规则）"""
    # 统计中文字符（含中文标点）
    chinese_count = len(re.findall(r"[\u4e00-\u9fa5\u3000-\u303f\uff00-\uffef]", text))
    # 统计英文单词（字母数字组合）
    english_words = re.findall(r"\b[a-zA-Z0-9]+\b", text)
    # 统计特殊符号（非中文、非字母数字的独立字符）
    special_chars = re.findall(r"(?<!\S)[^\w\u4e00-\u9fa5](?!\S)", text)

    return chinese_count + len(english_words) + len(special_chars)


def split_text_by_words(text, max_words, soft_words):
    """智能分块算法"""
    chunks = []
    current_count = 0
    buffer = []

    # 按自然断点分割
    sentences = re.split(r"([。！？；\.\?!;\n])", text)
    sentences = [s for s in sentences if s.strip()]

    for i in range(0, len(sentences), 2):
        sentence = sentences[i] + (sentences[i + 1] if i + 1 < len(sentences) else "")
        sentence_word_count = count_words(sentence)

        # 强制分割条件
        if current_count + sentence_word_count > max_words:
            if buffer:
                chunks.append("".join(buffer))
                buffer = []
                current_count = 0

        buffer.append(sentence)
        current_count += sentence_word_count

        # 软分割条件
        if current_count >= soft_words:
            chunks.append("".join(buffer))
            buffer = []
            current_count = 0

    if buffer:
        chunks.append("".join(buffer))
    return chunks


def find_balanced_split(text):
    """寻找最佳均分点"""
    mid = len(text) // 2
    split_chars = ["\n", "。", ";", "!", "?", "；"]

    # 向前查找
    for i in range(mid, min(mid + 300, len(text))):
        if text[i] in split_chars:
            return i + 1  # 包含分割符

    # 向后查找
    for i in range(mid, max(mid - 300, 0), -1):
        if text[i] in split_chars:
            return i + 1

    return mid


# ---- 文档结构处理 ----
def process_sections(data, MAX_CHUNK_WORDS, SOFT_CHUNK_WORDS, HARD_LIMIT):
    """处理章节结构"""
    processed = []
    current_title = None
    accumulated = []

    for item in data:
        if is_section_title(item):
            if current_title is not None:
                flush_section(current_title, accumulated, processed, MAX_CHUNK_WORDS, SOFT_CHUNK_WORDS, HARD_LIMIT)
            current_title = item["text"]
            accumulated = []
        else:
            accumulated.append(item["text"])

    flush_section(current_title, accumulated, processed, MAX_CHUNK_WORDS, SOFT_CHUNK_WORDS, HARD_LIMIT)
    return processed


def flush_section(title, parts, output, MAX_CHUNK_WORDS, SOFT_CHUNK_WORDS, HARD_LIMIT):
    """处理单个章节内容"""
    full_text = "\n".join(parts)
    if not full_text.strip():
        return

    word_count = count_words(full_text)

    if word_count <= MAX_CHUNK_WORDS:
        output.append(build_chunk(title, full_text))
    elif MAX_CHUNK_WORDS < word_count <= HARD_LIMIT:
        split_pos = find_balanced_split(full_text)
        output.append(build_chunk(title, full_text[:split_pos]))
        output.append(build_chunk(None, full_text[split_pos:]))
    else:
        chunks = split_text_by_words(full_text, MAX_CHUNK_WORDS, SOFT_CHUNK_WORDS)
        for i, chunk in enumerate(chunks):
            output.append(build_chunk(title if i == 0 else None, chunk))


def build_chunk(title, text):
    """构建分块结构"""
    if title:
        return {"type": "text", "text": f"{title}\n{text.strip()}"}
    return {"type": "text", "text": text.strip()}


def is_section_title(item):
    """判断是否为章节标题"""
    return item.get("type") == "text" and item.get("text_level") == 1


# 生成唯一占位符并记录映射
def generate_placeholder(element_type, content, placeholder_map):
    placeholder = element_placeholder[element_type] + f"_{len(placeholder_map)}"
    placeholder_map.append((placeholder, element_type, content))
    print(f"Generated placeholder: {placeholder} for {element_type} with content:\n{content}\n")
    return placeholder, placeholder_map


# 根据占位符还原文本内容
def restore_placeholders(text, placeholder_map):
    for placeholder, element_type, content in placeholder_map:
        if placeholder in text:
            # 直接替换为之前生成的内容
            text = text.replace(placeholder, content)
    return text


def merge_element(prev, current, placeholder_map):
    """
    * @description:
    # 合并元素：
       #   - 图像：用 Markdown 语法生成 "![](图片路径) 图片描述"，并与上文合并。
       #   - 表格：将表格描述（如 table_caption）添加在表格内容上方，与上文合并。
       #   - 公式：真公式与上下文合并（原逻辑不变）。假公式与下文合并
    * @param  prev :
    * @param  current :
    * @return
    """
    if current["type"] in ["equation", "image", "table"]:
        if current["type"] == "image":
            # 针对图像，取 img_path 和 img_caption
            img_path = current.get("img_path", "[Image path missing]")
            img_cap = current.get("img_caption")
            if isinstance(img_cap, list):
                img_caption_text = " ".join(img_cap) if img_cap else ""
            else:
                img_caption_text = img_cap if img_cap else ""
            # Markdown 格式：![](图片路径) 后接图片描述
            placeholder_content = f"![]({img_path}) {img_caption_text}"
        elif current["type"] == "table":
            # 针对表格，先获取描述（table_caption），若没有则为空
            table_caption = current.get("table_caption")
            if isinstance(table_caption, list):
                table_caption_text = " ".join(table_caption) if table_caption else ""
            else:
                table_caption_text = table_caption if table_caption else ""
            # 表格内容取 table_body，如不存在则尝试 text 字段
            table_body = current.get("table_body", current.get("text", "[Table content missing]"))
            # 生成内容：在表格上方添加描述，再换行后显示表格内容
            placeholder_content = f"{table_caption_text}\n{table_body}"
        else:  # equation
            placeholder_content = current.get("text", "[Equation]")

        # 生成占位符并记录映射
        placeholder, placeholder_map = generate_placeholder(current["type"], placeholder_content, placeholder_map)

        # 合并规则：
        # 公式与上下文合并；图像和表格只与上文合并
        if current["type"] == "equation":
            if prev and prev["type"] == "text":
                # 合并公式到上一个文本段，并标记为假性公式
                prev["text"] += PSEUDO_EQUATION_FLAG + placeholder
                prev["is_pseudo_equation"] = True  # 标记为假性公式
                return prev, None, placeholder_map
        else:
            if prev and prev["type"] == "text":
                prev["text"] += "\n" + placeholder + "\n"
                return prev, None, placeholder_map

    return prev, current, placeholder_map


def pre_handle_func(data):
    """
    * @description: 预处理数据
    * @param  data :
    * @return
    """
    # 如果第一个元素不是文本，则在最前面插入一个空文本项，确保有上文可以合并
    if data and data[0]["type"] != "text":
      data.insert(0, {"type": "text", "text": "", "text_level": 1})

    # 确保每个元素都有 "text" 和 "text_level" 键，避免 KeyError
    for item in data:
      if "text" not in item:
        item["text"] = ""
      if "text_level" not in item:
        item["text_level"] = 0

    # 过滤掉 "text" 为空的项，但保留 image、equation、table 类型的项以及 text_level 为 1 的项
    filtered_data = [
      item for item in data
      if item.get("text") != "" or item["type"] in ["image", "equation", "table"] or item.get("text_level") == 1
    ]
    processed_data = []
    previous_item = None
    placeholder_map = []
    # 主处理流程：合并文本、拆分长文本等
    for item in filtered_data:
        if previous_item:
            # 合并相邻的 "text_level": 1（标题连续），但如果文本中包含摘要或关键字，则不合并
            if previous_item["type"] == "text" and item["type"] == "text":
                if previous_item.get("text_level") == 1 and item.get("text_level") == 1:
                    previous_item["text"] += "-" + item["text"]
                    continue

            # 合并元素（图像、表格与上文，公式与上下文）
            previous_item, item, placeholder_map = merge_element(previous_item, item, placeholder_map)
            if item is None:
                continue

            # 处理假性公式的合并
            if previous_item.get("is_pseudo_equation", False):
                # 如果下一个文本段是标题，则不合并
                if item.get("text_level") == 1:
                    processed_data.append(previous_item)
                    previous_item = item
                    continue

                # 如果当前文本段加上下一个文本段的长度超过 1200，则不合并
                if len(previous_item["text"]) + len(item["text"]) > 1200:
                    processed_data.append(previous_item)
                    previous_item = item
                    continue

                # 否则，合并假性公式与下一个文本段
                previous_item["text"] += item["text"]
                previous_item["is_pseudo_equation"] = False  # 清除假性公式标志
                continue

            processed_data.append(previous_item)

        previous_item = item

    if previous_item:
        processed_data.append(previous_item)
    return processed_data, placeholder_map


def split_md_func(data, MAX_CHUNK_WORDS, SOFT_CHUNK_WORDS, HARD_LIMIT):
    """
    * @description: 主要流程, 整理
    * @param  data :
    * @param  MAX_CHUNK_WORDS :
    * @param  SOFT_CHUNK_WORDS :
    * @param  HARD_LIMIT :
    * @return
    """
    pre_handle_data, placeholder_map = pre_handle_func(data=data)

    middle_handle_data = process_sections(pre_handle_data, MAX_CHUNK_WORDS, SOFT_CHUNK_WORDS, HARD_LIMIT)
    # 统一恢复占位符，确保所有文本中的占位符都被正确替换
    for item in middle_handle_data:
        if item["type"] == "text":
            item["text"] = restore_placeholders(item["text"], placeholder_map)
    final_handle_data = middle_handle_data
    return final_handle_data


if __name__ == "__main__":
    ## config:
    MAX_CHUNK_WORDS = 1000
    SOFT_CHUNK_WORDS = 400
    HARD_LIMIT = 1400
    ##
    # with open("/media/disk0/xzzn_data_all/yinyabo/omni_split/test/c8d4614affc19ba92d7ba0671fd709803d0488a0c5a68bc237783a8af39fe32e/1c7fbb26-1012-4b03-894c-69ab2257985c_1743677710.4311144_content_list.json", "r", encoding="utf-8") as file:
    with open("1c7fbb26-1012-4b03-894c-69ab2257985c_1743677710.4311144_content_list.json", "r", encoding="utf-8") as file:

        data = json.load(file)
    final_handle_data = split_md_func(data, MAX_CHUNK_WORDS=MAX_CHUNK_WORDS, SOFT_CHUNK_WORDS=SOFT_CHUNK_WORDS, HARD_LIMIT=HARD_LIMIT)
    # 保存更新后的 JSON 文件
    with open("output4-yyb-en4.json", "w", encoding="utf-8") as file:
        json.dump(final_handle_data, file, ensure_ascii=False, indent=4)
