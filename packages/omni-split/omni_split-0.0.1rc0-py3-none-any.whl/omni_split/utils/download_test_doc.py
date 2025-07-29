import os
import requests
from typing import Dict

def download_files_to_test_doc() -> Dict[str, str]:
    """
    下载文件到 test_doc 文件夹，并返回 {文件名: 绝对路径} 的字典
    
    Args:
        file_list: 包含文件名和下载链接的字典，格式如 {"文件名": "下载链接"}
    
    Returns:
        返回一个字典，key 是文件名，value 是下载后的绝对路径
    """
    # 创建 test_doc 文件夹（如果不存在）
    file_list = {
        "docx_test.docx": "https://modelscope.cn/datasets/yinyabo/omni_split_test_doc/resolve/master/docx_test.docx",
        "json_list_test.json": "https://modelscope.cn/datasets/yinyabo/omni_split_test_doc/resolve/master/json_list_test.json",
        "markdown_test.md": "https://modelscope.cn/datasets/yinyabo/omni_split_test_doc/resolve/master/markdown_test.md",
        "text_test.txt": "https://modelscope.cn/datasets/yinyabo/omni_split_test_doc/resolve/master/text_test.txt"
    }
    os.makedirs("test_doc", exist_ok=True)
    
    result = {}
    
    def download_file(url: str, filename: str) -> str:
        """下载单个文件并返回其绝对路径"""
        try:
            response = requests.get(url, allow_redirects=True, stream=True)
            response.raise_for_status()
            
            filepath = os.path.abspath(os.path.join("test_doc", filename))
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"成功下载: {filename}")
            return filepath
        except Exception as e:
            print(f"下载 {filename} 失败: {str(e)}")
            return None
    
    # 下载所有文件
    for filename, url in file_list.items():
        absolute_path = download_file(url, filename)
        if absolute_path:
            result[filename] = absolute_path
    
    return result

# 使用示例
if __name__ == "__main__":
    # 定义要下载的文件列表

    
    # 调用函数下载文件
    downloaded_files = download_files_to_test_doc()
    
    # 打印结果
    print("\n下载结果：")
    for name, path in downloaded_files.items():
        print(f"{name}: {path}")