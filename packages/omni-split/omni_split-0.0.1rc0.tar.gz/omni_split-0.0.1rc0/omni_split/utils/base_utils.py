from io import BytesIO
from docx import Document
import os
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from loguru import logger
import re
import uuid
import base64

from wand.image import Image
from pathlib import Path
import warnings

def add_fix_before_extension(file_path):
    # 分割文件路径的目录、文件名和扩展名
    dir_name = os.path.dirname(file_path)
    base_name = os.path.basename(file_path)
    name, ext = os.path.splitext(base_name)

    # 在文件名和后缀之间添加 _fix
    new_name = f"{name}_fix{ext}"
    # 重新组合路径
    new_path = os.path.join(dir_name, new_name)
    return new_path


def delete_file(file_path):
    """删除指定路径的文件"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            # print(f"文件 {file_path} 已成功删除")
        else:
            pass
            # print(f"文件 {file_path} 不存在，无法删除")
    except Exception as e:
        print(f"删除文件 {file_path} 时出错: {e}")


def word_preprocessing_and_return_bytesIO(input_file):
    output_file = add_fix_before_extension(input_file)
    # 打开Word文档
    doc = Document(input_file)
    # 遍历文档中的所有段落
    for paragraph in doc.paragraphs:
        if "#" in paragraph.text:
            # 替换#为"!#"
            paragraph.text = paragraph.text.replace("#", r"\#")
    ## 将超链接部分替换为空字符串
    rels = doc.part.rels
    for rel in rels:
        if rels[rel].reltype == RT.HYPERLINK:
            # hyperlinks[rel] = rels[rel]._target
            rels[rel]._target = ""
    # 保存修改后的文档
    doc.save(output_file)
    with open(output_file, "rb") as f:
        doc_content = f.read()
        # 将bytes包装成BytesIO
        doc_content_io = BytesIO(doc_content)
    delete_file(output_file)
    return doc_content_io


def save_local_images_func(ret_data, image_save_path):
    """
    Process ret_data to extract Base64 images, save them locally, and update text references.

    Args:
        ret_data: List of dictionaries containing text with potential Base64 images
        image_save_path: Directory to save extracted images

    Returns:
        Modified ret_data with local image paths instead of Base64 strings
    """
    # Create directory if it doesn't exist
    if image_save_path and not os.path.exists(image_save_path):
        os.makedirs(image_save_path)

    # Regex pattern to match Base64 image strings
    base64_pattern = re.compile(r"!\[.*?\]\(data:(.*?);base64,(.*?)\)")

    for item in ret_data:
        if "text" not in item:
            continue

        text = item["text"]
        matches = base64_pattern.findall(text)

        if not matches:
            continue

        for match in list(set(matches)):
            native_format, img_data = match
            try:
                if native_format == "None":
                    img_format = "image/png"
                else:
                    img_format = native_format
                # Generate unique filename
                try:
                    filename = f"{uuid.uuid4()}.{img_format.split('/')[1].split(';')[0]}"
                except:
                    logger.info("img_format error, try to forcefully convert it to PNG.")
                    filename = f"{uuid.uuid4()}.png"
                filepath = os.path.join(image_save_path, filename)
                ## 最终要保存的local image path
                need_saved_filename = f"{uuid.uuid4()}.png"
                need_saved_filepath = os.path.join(image_save_path, need_saved_filename)

                # Decode and save image
                with open(filepath, "wb") as f:
                    f.write(base64.b64decode(img_data))

                convert_is_ok = convert_to_png(filepath, need_saved_filepath)

                # Replace Base64 string with file path
                if convert_is_ok:
                    text = text.replace(f"data:{native_format};base64,{img_data}", need_saved_filepath)
                else:
                    logger.info("convert_to_png error. save orginal file path.")
                    text = text.replace(f"data:{native_format};base64,{img_data}", filepath)
            except Exception as e:
                print(f"Failed to process image: {e}")
                continue

        item["text"] = text

    return ret_data





def convert_to_png(input_path: str, output_path: str) -> bool:
    """
    将输入图片文件（如 WMF/PNG/JPG）转换为 PNG 格式

    Args:
        input_path (str): 输入文件路径（如 "input.wmf" 或 "input.jpg"）
        output_path (str): 输出 PNG 文件路径（如 "output.png"）

    Returns:
        bool: 是否转换成功。如果ImageMagick未安装，直接返回False并保持原文件
    """
    try:
        # 检查wand是否能够正常工作（即ImageMagick是否安装）
        from wand.version import MAGICK_VERSION_INFO
    except (ImportError, ModuleNotFoundError) as e:
        warnings.warn(f"ImageMagick is not properly installed. Skipping conversion: {e}")
        return False
    except Exception as e:
        warnings.warn(f"Error checking ImageMagick installation: {e}")
        return False

    try:
        # 检查输入文件是否存在
        if not Path(input_path).is_file():
            print(f"Error: Input file '{input_path}' does not exist.")
            return False

        # 如果输出路径是目录，自动生成文件名
        output_path = str(Path(output_path))
        if Path(output_path).is_dir():
            output_path = str(Path(output_path) / (Path(input_path).stem + ".png"))

        # 使用 wand 进行转换
        with Image(filename=input_path) as img:
            img.format = "png"
            img.save(filename=output_path)

        print(f"Success: Converted '{input_path}' to '{output_path}'")
        return True

    except Exception as e:
        print(f"Error converting '{input_path}': {e}")
        return False


def download_tokenizer_from_network(ms=True):
    pass
