import os
from transformers import PreTrainedTokenizerFast
from .sub_chunker.document_split import DocumentChunker
from .sub_chunker.markdown_split import MarkdownChunker
from .sub_chunker.text_split import SentenceChunker
from .utils.base_utils import save_local_images_func
from importlib.resources import files

class OmniSplit:
    def __init__(self, tokenizer_json_path=None, txt_chunk_size=512):
        if tokenizer_json_path is None:
            # 获取当前文件的绝对路径，然后构建模型路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            tokenizer_json_path = os.path.join(current_dir, "model", "text_chunker_tokenizer","qwen_tokenizer.json")
        self.tokenizer_json_path = tokenizer_json_path
        self.txt_chunk_size = txt_chunk_size
        self.tokenizer = PreTrainedTokenizerFast(tokenizer_file=self.tokenizer_json_path)

    def get_text_len_func(self, text):
        """
        * @description: 获取文本长度
        * @param  self :
        * @param  text :
        * @return
        """
        if type(text) == str:
            return len(self.tokenizer.encode(text, add_special_tokens=False))
        else:
            raise ValueError("text must be str")

    def text_chunk_func(self, text, txt_chunk_size=None):
        """
        * @description: 纯文本的切割方法
        * @param  self :
        * @param  text :
        * @return
        """
        if txt_chunk_size is None:
            txt_chunk_size = self.txt_chunk_size
        text_chunker = SentenceChunker(tokenizer_or_token_counter=self.tokenizer, chunk_size=txt_chunk_size, delim=["!", "?", "\n", "。", ";", "；"], return_type="texts")
        temp_data_list  = text_chunker.chunk(text)
        ret_data = []
        for item in temp_data_list:
            ret_data.append({
                "type":"text",
                "text":item,
                "text_len":self.get_text_len_func(item)
            })
        return ret_data

    def markdown_json_chunk_func(self, markdown_json, txt_chunk_size=None, clear_model=False):
        if txt_chunk_size is None:
            txt_chunk_size = self.txt_chunk_size
        md_chunker = MarkdownChunker(max_chunk_words=txt_chunk_size, clear_model=clear_model)
        ret_data = md_chunker.convert_json_list2chunk_list_func(markdown_json)
        for item in ret_data:
            item["text_len"]= self.get_text_len_func(item["text"])
        return ret_data

    def markdown_chunk_func(self, markdown_text, txt_chunk_size=None, clear_model=False):
        """
        * @description: markdown的切割方法
        * @param  self :
        * @param  text :
        * @return
        """
        if txt_chunk_size is None:
            txt_chunk_size = self.txt_chunk_size
        md_chunker = MarkdownChunker(max_chunk_words=txt_chunk_size, clear_model=clear_model)
        ret_data = md_chunker.chunk(markdown_text)
        for item in ret_data:
            item["text_len"]= self.get_text_len_func(item["text"])
        return ret_data

    def document_chunk_func(self, document_content, txt_chunk_size=None, clear_model=False,save_local_images_dir=""):
        """
        * @description: office文档的切割方法
        * @param  self :
        * @param  text :
        * @return
        """
        if txt_chunk_size is None:
            txt_chunk_size = self.txt_chunk_size
        if save_local_images_dir=="":
            save_local_images_dir = save_local_images_dir
        doc_chunker = DocumentChunker(max_chunk_words=txt_chunk_size, clear_model=clear_model)
        ret_data = doc_chunker.chunk(document_content)

        if save_local_images_dir!="" and  not clear_model:
            ret_data = save_local_images_func(ret_data, save_local_images_dir)
        for item in ret_data:
            item["text_len"]= self.get_text_len_func(item["text"])
        return ret_data
