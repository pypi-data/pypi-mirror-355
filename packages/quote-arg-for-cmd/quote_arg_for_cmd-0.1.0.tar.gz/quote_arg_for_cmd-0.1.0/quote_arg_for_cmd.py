# -*- coding: utf-8 -*-
def escape_double_quotes_and_backslashes(chars):
    yield '"'

    backslash_buffer = []
    
    for char in chars:
        if char == '\\':
            backslash_buffer.append(char)
        elif char == '"':
            for _ in backslash_buffer: yield _
            for _ in backslash_buffer: yield _
            backslash_buffer = []

            yield '\\'
            yield '"'
        else:
            for _ in backslash_buffer: yield _
            backslash_buffer = []

            yield char
    
    for _ in backslash_buffer: yield _
    for _ in backslash_buffer: yield _
    backslash_buffer = []

    yield '"'


SPECIAL_CHARS_OUTSIDE_PAIRED_QUOTES = {'&', '|', '>', '<', '^'}

def escape_special_chars_outside_paired_quotes(chars):
    last_quote_index = None
    is_inside_paired_quotes = False
    
    for i, char in enumerate(chars):
        if char == '"':
            if last_quote_index is None:
                last_quote_index = i
                is_inside_paired_quotes = True
            else:
                last_quote_index = None
                is_inside_paired_quotes = False
        elif char in SPECIAL_CHARS_OUTSIDE_PAIRED_QUOTES and not is_inside_paired_quotes:
            yield '^'
        
        yield char


def quote_arg_for_cmd(string):
    return ''.join(
        escape_special_chars_outside_paired_quotes(
            escape_double_quotes_and_backslashes(string)
        )
    )
