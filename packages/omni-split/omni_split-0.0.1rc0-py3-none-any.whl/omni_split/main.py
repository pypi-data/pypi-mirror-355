import json
from omni_split import OmniSplit
from omni_split import word_preprocessing_and_return_bytesIO

omni_spliter = OmniSplit()
## note: test text split
test_text = True
if test_text:
    with open("omni_split/test/text_test.txt", "r") as f:
        text_content = "".join(f.readlines())
    res = omni_spliter.text_chunk_func(text_content)
    for item in res:
        print(item)
        print("------------")
    print("=" * 10)

## note: test markdown json split
test_markdown = True
if test_markdown:
    with open("omni_split/test/json_list_test.json", "r") as f:
        md_content_json = json.load(f)
    res = omni_spliter.markdown_json_chunk_func(md_content_json)
    for item in res:
        print(item)
        print("------------")
    print("=" * 10)

    res = omni_spliter.markdown_json_chunk_func(md_content_json, clear_model=True)
    for item in res:
        print(item)
        print("------------")
    print("=" * 10)

## note: test markdown split
test_markdown = True
if test_markdown:
    with open("omni_split/test/markdown_test.md", "r") as f:
        md_content = f.read()
    res = omni_spliter.markdown_chunk_func(md_content)
    for item in res:
        print(item)
        print("------------")
    print("=" * 10)

    res = omni_spliter.markdown_chunk_func(md_content, clear_model=True)
    for item in res:
        print(item)
        print("------------")
    print("=" * 10)


## note: test word split
test_document = True
if test_document:

    new_doc_io = word_preprocessing_and_return_bytesIO("omni_split/test/docx_test.docx")
    res = omni_spliter.document_chunk_func(new_doc_io, txt_chunk_size=1000, clear_model=False)
    for item in res:
        print(item)
        print("------------")
    print("=" * 10)

    res = omni_spliter.document_chunk_func(new_doc_io, txt_chunk_size=1000, clear_model=False, save_local_images_dir="./images")
    for item in res:
        print(item)
        print("------------")
    print("=" * 10)

    res = omni_spliter.document_chunk_func(new_doc_io, txt_chunk_size=1000, clear_model=True)
    for item in res:
        print(item)
        print("------------")
    print("=" * 10)
