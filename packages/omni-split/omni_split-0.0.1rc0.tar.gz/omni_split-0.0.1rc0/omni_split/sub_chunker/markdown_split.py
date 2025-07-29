from ..base.md_json_list2chunk import markdown_json_list2chunk_list
from ..base.md2json_list import md2json_list_func


class MarkdownChunker:
    def __init__(self, max_chunk_words=1000, soft_chunk_words=None, hard_limit=None, clear_model=False):
        self.max_chunk_words = max_chunk_words
        if soft_chunk_words is None:
            self.soft_chunk_words = max_chunk_words * 0.4
        else:
            self.soft_chunk_words = soft_chunk_words
        if hard_limit is None:
            self.hard_limit = max_chunk_words * 1.4
        else:
            self.hard_limit = hard_limit
        self.clear_model = clear_model
        ## 
        # self.chunk_markdown_json = self.convert_json_list2chunk_list_func
    def convert_markdown2json_list_func(self, markdown_text):
        markdown_json_list = md2json_list_func(markdown_text)
        assert type(markdown_json_list) == list
        return markdown_json_list

    def convert_json_list2chunk_list_func(self, json_list):
        if self.clear_model:
            ## todo: 处理特殊模式(清理不可以embedding的内容, 如图片)
            json_clear_list = []
            for item in json_list:
                if item["type"] == "image":
                    continue
                # note: 其他的按照标准text对待.
                json_clear_list.append(item)
            json_list = json_clear_list
        chunk_list = markdown_json_list2chunk_list(json_list, MAX_CHUNK_WORDS=self.max_chunk_words, SOFT_CHUNK_WORDS=self.soft_chunk_words, HARD_LIMIT=self.hard_limit)
        return chunk_list
    
    def chunk(self, text_content):
        markdown_json_list = self.convert_markdown2json_list_func(text_content)
        for item in markdown_json_list:
            if item.get("text_level",None) is not None:
                item["text_level"] = 1
        chunk_list = self.convert_json_list2chunk_list_func(markdown_json_list)
        assert type(markdown_json_list) == list
        return chunk_list
# import json
# with open("temp.json","w") as f:
#     json.dump(markdown_json_list,f,ensure_ascii=False,indent=4)