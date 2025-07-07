from typing import Tuple

from extractor.extractor_base import Extractor


class PyExtractor(Extractor):

    def __init__(self, code):
        super().__init__(code, 'python')
        self.lang = "py"

    @property
    def token_type_black_list(self) -> Tuple:
        return "comment", "string_start",  "string_end", "string_content"

    @property
    def token_type_str_list(self) -> Tuple:
        return ("string_content",)
