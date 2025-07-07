from .bash_extractor import BashExtractor
from .js_extractor import JSExtractor
from .py_extractor import PyExtractor
from .extractor_base import Extractor
from .extractor_base import keywords_len
from .package_extractor import PackageExtractor
from .utils import purify_bash_code, remove_setup_args


def extract_code(code: bytes, lang) -> Extractor:
    if lang == "js":
        return JSExtractor(code)
    elif lang == "py":
        return PyExtractor(code)
    elif lang == "sh":
        return BashExtractor(code)
    else:
        raise NotImplementedError(f"The lang {lang} is not supported")
