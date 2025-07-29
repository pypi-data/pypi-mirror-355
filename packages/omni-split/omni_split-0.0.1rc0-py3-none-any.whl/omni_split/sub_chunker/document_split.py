from markitdown import MarkItDown
from .markdown_split import MarkdownChunker


class DocumentChunker:
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
        self.markitdown = MarkItDown(enable_plugins=False)
        self.markdown_chunker = MarkdownChunker(max_chunk_words=self.max_chunk_words, clear_model=self.clear_model)

    def convert_document2md_func(self, document_content):

        # print("convert_document2md_func")
        # print()
        markdown_result = self.markitdown.convert(document_content,keep_data_uris=True)
        content = markdown_result.markdown
        return content

    def chunk(self, document_content):
        markdown_text = self.convert_document2md_func(document_content)
        chunk_list = self.markdown_chunker.chunk(markdown_text)
        assert type(chunk_list) == list
        return chunk_list
