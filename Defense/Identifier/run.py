import argparse
import json
from os import replace
import sys
sys.path.append('./python_parser/')
from tqdm import tqdm

from parser_folder.DFG_java import DFG_java
from parser_folder import (remove_comments_and_docstrings,
                           tree_to_token_index,
                           index_to_code_token,)
from tree_sitter import Language, Parser
import os

java_keywords = ["abstract", "assert", "boolean", "break", "byte", "case", "catch", "do", "double", "else", "enum",
                 "extends", "final", "finally", "float", "for", "goto", "if", "implements", "import", "instanceof",
                 "int", "interface", "long", "native", "new", "package", "private", "protected", "public", "return",
                 "short", "static", "strictfp", "super", "switch", "throws", "transient", "try", "void", "volatile",
                 "while"]
java_special_ids = ["main", "args", "Math", "System", "Random", "Byte", "Short", "Integer", "Long", "Float", "Double", "Character",
                    "Boolean", "Data", "ParseException", "SimpleDateFormat", "Calendar", "Object", "String", "StringBuffer",
                    "StringBuilder", "DateFormat", "Collection", "List", "Map", "Set", "Queue", "ArrayList", "HashSet", "HashMap"]

special_char = ['[', ']', ':', ',', '.', '(', ')', '{', '}', 'not', 'is', '=', "+=", '-=', "<", ">", '+', '-', '*', '/',
                '|']

from keyword import iskeyword
def is_valid_variable_python(name: str) -> bool:
    return name.isidentifier() and not iskeyword(name)

def is_valid_variable_java(name: str) -> bool:
    if not name.isidentifier():
        return False
    elif name in java_keywords:
        return False
    elif name in java_special_ids:
        return False
    return True

def is_valid_variable_c(name: str) -> bool:

    if not name.isidentifier():
        return False
    return True

def is_valid_variable_name(name: str, lang: str) -> bool:
    # check if matches language keywords
    if lang == 'java':
        return is_valid_variable_java(name)
    else:
        return False

path = './python_parser/parser_folder/my-languages.so'
# path = 'parser_folder/my-languages.so'

dfg_function = {
    'java': DFG_java
}


LANG_LIB_MAP = {
    'java': 'tree_sitter_assets/java.so'
}

LANG_REPO_MAP = {
    'java': 'tree-sitter-java'
}

if not os.path.exists(path):
    for lang in LANG_LIB_MAP:
        print(f'Installing {lang} language library...')
        if not os.path.exists(LANG_REPO_MAP[lang]):
            os.popen(
                f'git clone https://github.com/tree-sitter/{LANG_REPO_MAP[lang]}.git'
            ).read()
    Language.build_library(path, list(LANG_REPO_MAP.values()))



# load parsers
parsers = {}
for lang in dfg_function:
    LANGUAGE = Language(path, lang)
    parser = Parser()
    parser.set_language(LANGUAGE)
    parser = [parser, dfg_function[lang]]
    parsers[lang] = parser

codes = {}

def get_code_tokens(code, lang):
    code = code.split('\n')
    code_tokens = [x + '\\n' for x in code if x ]
    return code_tokens

def extract_dataflow(code, lang):
    parser = parsers[lang]
    code = code.replace("\\n", "\n")
    # remove comments
    try:
        code = remove_comments_and_docstrings(code, lang)
    except:
        pass
    parser = parsers[lang]
    tree = parser[0].parse(bytes(code, 'utf8'))
    root_node = tree.root_node
    tokens_index = tree_to_token_index(root_node)
    code = code.split('\n')
    # print(code)
    code_tokens = [index_to_code_token(x, code) for x in tokens_index]
    index_to_code = {}
    for idx, (index, code) in enumerate(zip(tokens_index, code_tokens)):
        index_to_code[index] = (idx, code)

    index_table = {}
    for idx, (index, code) in enumerate(zip(tokens_index, code_tokens)):
        index_table[idx] = index

    DFG, _ = parser[1](root_node, index_to_code, {})

    DFG = sorted(DFG, key=lambda x: x[1])
    return DFG, index_table, code_tokens


def get_example(code, tgt_word, substitute, lang):
    code = code.replace("\\n", "\n")
    parser = parsers[lang]
    tree = parser[0].parse(bytes(code, 'utf8'))
    root_node = tree.root_node
    tokens_index = tree_to_token_index(root_node)
    code = code.split('\n')
    code_tokens = [index_to_code_token(x, code) for x in tokens_index]
    replace_pos = {}
    for index, code_token in enumerate(code_tokens):
        if code_token == tgt_word:
            try:
                replace_pos[tokens_index[index][0][0]].append((tokens_index[index][0][1], tokens_index[index][1][1]))
            except:
                replace_pos[tokens_index[index][0][0]] = [(tokens_index[index][0][1], tokens_index[index][1][1])]
    diff = len(substitute) - len(tgt_word)

    for line in replace_pos.keys():
        for index, pos in enumerate(replace_pos[line]):
            code[line] = code[line][:pos[0] + index * diff] + substitute + code[line][pos[1] + index * diff:]
    return "\n".join(code)


def unique(sequence):
    seen = set()
    return [x for x in sequence if not (x in seen or seen.add(x))]

def get_identifiers(code, lang):
    dfg, index_table, code_tokens = extract_dataflow(code, lang)
    ret = []
    for d in dfg:
        if is_valid_variable_name(d[0], lang):
            ret.append(d[0])
    ret = unique(ret)
    ret = [ i for i in ret]
    return ret, code_tokens


def change_identifiers(input_code):
    identifiers, _ = get_identifiers(input_code, "java")
    substituted_code = input_code

    for i, identifier in enumerate(identifiers, start=1):
        substituted_code = get_example(substituted_code, identifier, f'Var{i}', "java")
    return substituted_code

