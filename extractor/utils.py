import ast
import re
from itertools import chain
from typing import List, Tuple, Sized, Iterable, Union

import astunparse
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from tree_sitter_languages import get_parser
from urlextract import URLExtract


class Tree:

    def __init__(self, code: bytes, language_str):
        parser = get_parser(language_str)
        self.tree = parser.parse(code)

    def traverse_tree_iter(self):
        cursor = self.tree.walk()

        visited_children = None
        while True:
            if not visited_children:
                yield cursor.node
                if not cursor.goto_first_child():
                    visited_children = True
            elif cursor.goto_next_sibling():
                visited_children = False
            elif not cursor.goto_parent():
                break

    def __iter__(self):
        return self.traverse_tree_iter()


class TargetAPI(Iterable, Sized):

    def __init__(self, *api_lists: Union[List, Tuple]):
        self.total_target_apis_set = set(chain(*api_lists))
        self.total_target_apis = tuple(self.total_target_apis_set)
        self.api_to_index = {id_: number for id_, number in
                             zip(self.total_target_apis, range(len(self.total_target_apis)))}

    def __iter__(self):
        return self.total_target_apis

    def __len__(self):
        return len(self.total_target_apis)

    def __contains__(self, item):
        return item in self.total_target_apis_set

    def find(self, item):
        return self.api_to_index[item] if item in self.api_to_index else -1


def purify_bash_code(bash_line: bytes) -> bytes:
    # remove js/ts files
    bash_line = bash_line.decode('utf-8', errors='ignore')

    known_appendix = ("js", "ts", "py", "sh", "bat", "ps1")

    pattern = re.compile(
        r'\b([^\s/\\]+?)\.(' + '|'.join(map(re.escape, known_appendix)) + r')\b',
        flags=re.IGNORECASE
    )

    bash_line = ILLEGAL_CHARACTERS_RE.sub("", bash_line)  # remove illegal chars

    new_bash_line = pattern.sub(r'\2_file.\2', bash_line)

    bash_line = new_bash_line

    url_extractor = URLExtract()
    url_extractor.ignore_list = [f'{appendix}_file.{appendix}' for appendix in known_appendix]
    for url in url_extractor.gen_urls(bash_line):
        bash_line = bash_line.replace(url, "norm.url.com")

    # /dev/tcp/
    pattern = r"/dev/tcp/[^/]+/\d+"
    bash_line = re.sub(pattern, "/dev/tcp/mal.host/666", bash_line)

    return bash_line.encode('utf-8')


def remove_setup_args(content):
    content = content.decode('utf-8')
    try:
        tree = ast.parse(content)

        class SetupArgsRemover(ast.NodeTransformer):
            def visit_Call(self, node):
                if isinstance(node.func, ast.Name) and node.func.id == 'setup':
                    # 移除所有参数
                    node.args = []
                    node.keywords = []
                return self.generic_visit(node)

        transformer = SetupArgsRemover()
        new_tree = transformer.visit(tree)
        new_tree = ast.fix_missing_locations(new_tree)

        return astunparse.unparse(new_tree).encode()
    except:
        print("AST failed!, using regex instead")
        setup_call = re.search(r'setup\(([^)]*)\)', content)

        if setup_call:
            new_content = content.replace(setup_call.group(0), 'setup()')
        else:
            new_content = content

        return new_content.encode()
