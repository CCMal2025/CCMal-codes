from typing import Tuple

from .extractor_base import Extractor


class BashExtractor(Extractor):

    def __init__(self, code):
        super().__init__(code, 'bash')
        self.lang = "sh"

    @property
    def token_type_black_list(self) -> Tuple:
        return 'raw_string', 'string_content', 'comment'

    @property
    def token_type_str_list(self) -> Tuple:
        return 'raw_string', 'string_content'
