from typing import Tuple

from extractor.extractor_base import Extractor


class JSExtractor(Extractor):

    def __init__(self, code: bytes):
        super().__init__(code, 'javascript')
        self.lang = "js"

    @property
    def token_type_black_list(self) -> Tuple:
        return "comment", "'", '"', ";", "string_fragment"

    @property
    def token_type_str_list(self) -> Tuple:
        return ("string_fragment",)
