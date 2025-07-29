from .omni_split import OmniSplit
from .utils.base_utils import word_preprocessing_and_return_bytesIO
from .utils.download_test_doc import download_files_to_test_doc

__version__ = "0.0.1"
__name__ = "omni_split"
__author__ = "dinobot22"

__all__ = [
    "__name__",
    "__version__",
    "__author__",
    "OmniSplit",
    "word_preprocessing_and_return_bytesIO",
    "download_files_to_test_doc"
]
