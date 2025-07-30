"""
Pygments TLDR Formatter

A formatter for Pygments that outputs TLDR-formatted code with syntax highlighting
using fenced code blocks and optional inline styling.
"""
import logging

from pygments_tldr.formatter import Formatter
from pygments_tldr.token import (
    Token, Whitespace, Error, Other, Keyword, Name, Literal, String,
    Number, Punctuation, Operator, Comment, Generic
)
from pygments_tldr.util import get_bool_opt, get_int_opt, get_list_opt


class TLDRFormatter(Formatter):
    """
    Format tokens as TLDR code blocks with optional syntax highlighting.

    This formatter outputs code in TLDR format using fenced
    code blocks (```). It supports various options for customization including
    language specification, line numbers, and inline formatting.

    Options accepted:

    `lang` : string
        The language identifier to use in the fenced code block.
        If not specified, attempts to detect from lexer name.

    `linenos` : bool
        Turn on line numbers. (default: False)

    `linenostart` : integer
        The line number for the first line (default: 1)

    `hl_lines` : list of integers
        Specify a list of lines to be highlighted with comments.

    `full` : bool
        Generate a complete TLDR document with title and metadata.
        (default: False)

    `title` : string
        Title for the document when `full` is True. (default: '')

    `inline_styles` : bool
        Use inline TLDR formatting for syntax highlighting instead of
        just the fenced code block. (default: False)

    `fence_char` : string
        Character to use for fencing. Either '`' or '~'. (default: '`')

    `fence_count` : integer
        Number of fence characters to use. Must be at least 3. (default: 3)

    `highlight_functions` : bool
        Add special highlighting for function/method signatures

    """

    name = 'TLDR'
    aliases = ['tldr', 'TLDR']
    filenames = ['*.*']

    def __init__(self, **options):
        Formatter.__init__(self, **options)

        # Basic options
        self.lang = options.get('lang', '')
        self.linenos = get_bool_opt(options, 'linenos', False)
        self.linenostart = get_int_opt(options, 'linenostart', 1)
        self.hl_lines = set(get_list_opt(options, 'hl_lines', []))
        self.inline_styles = get_bool_opt(options, 'inline_styles', False)

        # Markdown-specific options
        self.fence_char = options.get('fence_char', '`')
        if self.fence_char not in ('`', '~'):
            self.fence_char = '`'

        self.fence_count = get_int_opt(options, 'fence_count', 3)
        if self.fence_count < 3:
            self.fence_count = 3

        # Function highlighting options
        self.highlight_functions = get_bool_opt(options, 'highlight_functions', True)

        # Auto-detect language if not specified
        if not self.lang and hasattr(self, 'lexer'):
            if hasattr(self.lexer, 'aliases') and self.lexer.aliases:
                self.lang = self.lexer.aliases[0]
            elif hasattr(self.lexer, 'name'):
                self.lang = self.lexer.name.lower()

    def _get_markdown_style(self, ttype):
        """
        Convert Pygments token types to Markdown inline formatting.
        Returns a tuple of (prefix, suffix) strings.
        """
        if not self.inline_styles:
            return ('', '')

        # Map token types to Markdown formatting
        style_map = {
            # Comments - italic
            Comment: ('*', '*'),
            Comment.Single: ('*', '*'),
            Comment.Multiline: ('*', '*'),
            Comment.Preproc: ('*', '*'),
            Comment.PreprocFile: ('*', '*'),
            Comment.Special: ('*', '*'),

            # Keywords - bold
            Keyword: ('**', '**'),
            Keyword.Constant: ('**', '**'),
            Keyword.Declaration: ('**', '**'),
            Keyword.Namespace: ('**', '**'),
            Keyword.Pseudo: ('**', '**'),
            Keyword.Reserved: ('**', '**'),
            Keyword.Type: ('**', '**'),

            # Strings - no special formatting (already in code block)
            String: ('', ''),
            String.Backtick: ('', ''),
            String.Char: ('', ''),
            String.Doc: ('', ''),
            String.Double: ('', ''),
            String.Escape: ('', ''),
            String.Heredoc: ('', ''),
            String.Interpol: ('', ''),
            String.Other: ('', ''),
            String.Regex: ('', ''),
            String.Single: ('', ''),
            String.Symbol: ('', ''),

            # Names - no special formatting
            Name: ('', ''),
            Name.Attribute: ('', ''),
            Name.Builtin: ('', ''),
            Name.Builtin.Pseudo: ('', ''),
            Name.Class: ('', ''),
            Name.Constant: ('', ''),
            Name.Decorator: ('', ''),
            Name.Entity: ('', ''),
            Name.Exception: ('', ''),
            Name.Function: ('', ''),
            Name.Function.Magic: ('', ''),
            Name.Label: ('', ''),
            Name.Namespace: ('', ''),
            Name.Other: ('', ''),
            Name.Property: ('', ''),
            Name.Tag: ('', ''),
            Name.Variable: ('', ''),
            Name.Variable.Class: ('', ''),
            Name.Variable.Global: ('', ''),
            Name.Variable.Instance: ('', ''),
            Name.Variable.Magic: ('', ''),

            # Numbers - no special formatting
            Number: ('', ''),
            Number.Bin: ('', ''),
            Number.Float: ('', ''),
            Number.Hex: ('', ''),
            Number.Integer: ('', ''),
            Number.Integer.Long: ('', ''),
            Number.Oct: ('', ''),

            # Operators and punctuation - no special formatting
            Operator: ('', ''),
            Operator.Word: ('', ''),
            Punctuation: ('', ''),

            # Preprocessor - italic
            # Preprocessor: ('*', '*'),

            # Errors - strikethrough (if supported)
            Error: ('~~', '~~'),

            # Generic tokens
            Generic: ('', ''),
            Generic.Deleted: ('~~', '~~'),
            Generic.Emph: ('*', '*'),
            Generic.Error: ('~~', '~~'),
            Generic.Heading: ('**', '**'),
            Generic.Inserted: ('', ''),
            Generic.Output: ('', ''),
            Generic.Prompt: ('**', '**'),
            Generic.Strong: ('**', '**'),
            Generic.Subheading: ('**', '**'),
            Generic.Traceback: ('*', '*'),
        }

        return style_map.get(ttype, ('', ''))

    def _is_function_definition(self, tokens, start_idx):
        """
        Detect if the current position is the start of a function/method definition.
        Returns (is_function, function_name, parameters, end_idx, access_modifier, return_type) tuple.
        """
        if not self.highlight_functions:
            return False, None, None, start_idx, None, None

        # Look for common function definition patterns
        i = start_idx
        function_name = ""
        parameters = ""
        access_modifier = ""
        return_type = ""
        found_def = False
        found_name = False
        paren_count = 0

        # Skip whitespace at the beginning
        while i < len(tokens) and tokens[i][0] in (Whitespace,):
            i += 1

        if i >= len(tokens):
            return False, None, None, start_idx, None, None

        # Look backwards for access modifiers and return types
        # This helps capture patterns like "public static int myFunction()"
        access_modifiers = []
        return_types = []

        # Look back up to 10 tokens for modifiers/types
        lookback_start = max(0, start_idx - 10)
        for j in range(lookback_start, i):
            if j < len(tokens):
                ttype, value = tokens[j]
                if ttype == Keyword and value.lower() in ('public', 'private', 'protected', 'static', 'final', 'abstract', 'virtual', 'override', 'async', 'extern'):
                    access_modifiers.append(value)
                elif ttype in (Keyword.Type, Name.Builtin.Type, Keyword) and value.lower() in ('void', 'int', 'string', 'bool', 'float', 'double', 'long', 'short', 'char', 'byte'):
                    return_types.append(value)
                elif ttype == Name and value in ('String', 'Integer', 'Boolean', 'List', 'Dict', 'Array'):
                    return_types.append(value)

        # Look for function definition patterns
        ttype, value = tokens[i]
        is_arrow_function = False
        
        # Method 1: Look for Name.Function token (Python, some other languages)
        if ttype == Name.Function or ttype == Name.Function.Magic:
            # High confidence this is a function definition
            function_name = value
            found_name = True
            logging.debug(f"Found function definition (Name.Function): {function_name}")
            i += 1
        
        # Method 2: Look for JavaScript/TypeScript function patterns
        elif ttype == Keyword.Declaration and value == 'function':
            # Look for the function name after the 'function' keyword
            i += 1
            # Skip whitespace
            while i < len(tokens) and tokens[i][0] in (Whitespace,):
                i += 1
            
            if i < len(tokens):
                next_ttype, next_value = tokens[i]
                if next_ttype in (Name.Other, Name):
                    function_name = next_value
                    found_name = True
                    logging.debug(f"Found function definition (JS function): {function_name}")
                    i += 1
        
        # Method 2b: Look for export function patterns
        elif ttype == Keyword and value == 'export':
            # Look ahead for 'function' keyword
            temp_i = i + 1
            while temp_i < len(tokens) and tokens[temp_i][0] in (Whitespace,):
                temp_i += 1
            
            if temp_i < len(tokens) and tokens[temp_i][0] == Keyword.Declaration and tokens[temp_i][1] == 'function':
                # Found export function, look for the function name
                temp_i += 1
                while temp_i < len(tokens) and tokens[temp_i][0] in (Whitespace,):
                    temp_i += 1
                
                if temp_i < len(tokens) and tokens[temp_i][0] in (Name.Other, Name):
                    function_name = tokens[temp_i][1]
                    found_name = True
                    logging.debug(f"Found export function definition: {function_name}")
                    i = temp_i + 1
        
        # Method 3: Look for const/let/var arrow functions
        elif ttype in (Keyword.Declaration, Keyword) and value in ('const', 'let', 'var'):
            # Look ahead for arrow function pattern: const name = (...) => {...}
            temp_i = i + 1
            potential_name = ""
            
            # Skip whitespace and get the name
            while temp_i < len(tokens) and tokens[temp_i][0] in (Whitespace,):
                temp_i += 1
            if temp_i < len(tokens) and tokens[temp_i][0] in (Name.Other, Name):
                potential_name = tokens[temp_i][1]
                temp_i += 1
            
            # Look for = ... => pattern
            found_arrow = False
            paren_depth = 0
            while temp_i < len(tokens) and temp_i < i + 20:  # Limit search range
                temp_ttype, temp_value = tokens[temp_i]
                if temp_value == '=' and paren_depth == 0:
                    # Found assignment, look for arrow function
                    temp_i += 1
                    while temp_i < len(tokens) and tokens[temp_i][0] in (Whitespace,):
                        temp_i += 1
                    
                    # Check for different arrow function patterns
                    arrow_start = temp_i
                    while temp_i < len(tokens) and temp_i < arrow_start + 10:
                        temp_ttype, temp_value = tokens[temp_i]
                        if temp_value == '=>':
                            found_arrow = True
                            break
                        elif temp_value == '(':
                            paren_depth += 1
                        elif temp_value == ')':
                            paren_depth -= 1
                        temp_i += 1
                    break
                elif temp_value == '(':
                    paren_depth += 1
                elif temp_value == ')':
                    paren_depth -= 1
                temp_i += 1
            
            if found_arrow and potential_name:
                function_name = potential_name
                found_name = True
                is_arrow_function = True
                logging.debug(f"Found arrow function definition: {function_name}")
                # Position after the name
                i += 1
                while i < len(tokens) and tokens[i][0] in (Whitespace,):
                    i += 1
                if i < len(tokens) and tokens[i][0] in (Name.Other, Name):
                    i += 1

            # Look forward for return type annotations (like Python type hints: -> int)
            temp_i = i
            while temp_i < len(tokens) and tokens[temp_i][0] in (Whitespace,):
                temp_i += 1

            # Check for opening paren first
            if temp_i < len(tokens) and tokens[temp_i][1] == '(':
                # Skip to after the closing paren to look for return type
                paren_depth = 1
                temp_i += 1
                while temp_i < len(tokens) and paren_depth > 0:
                    if tokens[temp_i][1] == '(':
                        paren_depth += 1
                    elif tokens[temp_i][1] == ')':
                        paren_depth -= 1
                    temp_i += 1

                # Now look for return type annotation (-> Type)
                while temp_i < len(tokens) and tokens[temp_i][0] in (Whitespace,):
                    temp_i += 1

                if temp_i < len(tokens) - 1:
                    if tokens[temp_i][1] == '-' and temp_i + 1 < len(tokens) and tokens[temp_i + 1][1] == '>':
                        # Found -> annotation, get the return type
                        temp_i += 2
                        while temp_i < len(tokens) and tokens[temp_i][0] in (Whitespace,):
                            temp_i += 1
                        if temp_i < len(tokens) and tokens[temp_i][0] in (Name, Name.Builtin, Keyword.Type):
                            return_types.append(tokens[temp_i][1])

        if not found_name:
            return False, None, None, start_idx, None, None

        # Combine modifiers and return types
        access_modifier = ' '.join(access_modifiers) if access_modifiers else None
        return_type = ' '.join(return_types) if return_types else None

        # For arrow functions, look for the parameter pattern differently
        if is_arrow_function:
            # This is an arrow function, extract parameters differently
            temp_i = i
            while temp_i < len(tokens):
                temp_ttype, temp_value = tokens[temp_i]
                if temp_value == '=':
                    temp_i += 1
                    while temp_i < len(tokens) and tokens[temp_i][0] in (Whitespace,):
                        temp_i += 1
                    
                    # Look for parameter pattern: () or (param1, param2) or param
                    if temp_i < len(tokens) and tokens[temp_i][1] == '(':
                        # Extract parameters from parentheses
                        paren_count = 1
                        temp_i += 1
                        param_tokens = []
                        
                        while temp_i < len(tokens) and paren_count > 0:
                            temp_ttype, temp_value = tokens[temp_i]
                            if temp_value == '(':
                                paren_count += 1
                            elif temp_value == ')':
                                paren_count -= 1
                            
                            if paren_count > 0:
                                param_tokens.append((temp_ttype, temp_value))
                            temp_i += 1
                        
                        parameters = ''.join(token[1] for token in param_tokens).strip()
                        parameters = ' '.join(parameters.split())
                        
                        # Look for the arrow
                        while temp_i < len(tokens) and tokens[temp_i][0] in (Whitespace,):
                            temp_i += 1
                        if temp_i < len(tokens) and tokens[temp_i][1] == '=>':
                            return True, function_name, parameters, temp_i, access_modifier, return_type
                    else:
                        # Single parameter without parentheses
                        param_start = temp_i
                        while temp_i < len(tokens) and tokens[temp_i][1] != '=>':
                            temp_i += 1
                        if temp_i < len(tokens):
                            param_tokens = tokens[param_start:temp_i]
                            parameters = ''.join(token[1] for token in param_tokens).strip()
                            parameters = ' '.join(parameters.split())
                            return True, function_name, parameters, temp_i, access_modifier, return_type
                    break
                temp_i += 1
        
        # Look for opening parenthesis to confirm it's a function (traditional functions)
        # First, skip over any generic type parameters (e.g., <T>)
        generic_start = i
        while i < len(tokens):
            ttype, value = tokens[i]
            if ttype == Punctuation and value == '<':
                # Skip over generic type parameters
                angle_count = 1
                i += 1
                while i < len(tokens) and angle_count > 0:
                    ttype, value = tokens[i]
                    if ttype == Punctuation:
                        if value == '<':
                            angle_count += 1
                        elif value == '>':
                            angle_count -= 1
                    i += 1
                break
            elif ttype == Punctuation and value == '(':
                break
            elif ttype not in (Whitespace,):
                # Skip over other tokens until we find ( or <
                i += 1
                if i >= len(tokens):
                    break
            else:
                i += 1

        # Now look for the opening parenthesis
        while i < len(tokens):
            ttype, value = tokens[i]
            if ttype == Punctuation and value == '(':
                # Found function signature, now extract parameters
                paren_count = 1
                i += 1
                param_tokens = []

                while i < len(tokens) and paren_count > 0:
                    ttype, value = tokens[i]
                    if ttype == Punctuation:
                        if value == '(':
                            paren_count += 1
                        elif value == ')':
                            paren_count -= 1

                    # Collect parameter tokens (exclude the closing parenthesis)
                    if paren_count > 0:
                        param_tokens.append((ttype, value))

                    i += 1

                # Extract parameter string
                parameters = ''.join(token[1] for token in param_tokens).strip()
                # Clean up parameters - remove newlines and extra spaces
                parameters = ' '.join(parameters.split())

                # Look for TypeScript return type annotation (: Type)
                return_type_tokens = []
                while i < len(tokens):
                    ttype, value = tokens[i]
                    if ttype == Punctuation and value == ':':
                        # Found return type annotation, collect tokens until { or ;
                        i += 1
                        while i < len(tokens):
                            ttype, value = tokens[i]
                            if value in ('{', ';') or value == '\n':
                                break
                            return_type_tokens.append((ttype, value))
                            i += 1
                        
                        if return_type_tokens:
                            return_type = ''.join(token[1] for token in return_type_tokens).strip()
                            return_type = ' '.join(return_type.split())
                        
                        return True, function_name, parameters, i, access_modifier, return_type
                    elif value in ('{', ';') or value == '\n':
                        return True, function_name, parameters, i, access_modifier, return_type
                    i += 1

                return True, function_name, parameters, i, access_modifier, return_type
            elif ttype not in (Whitespace,):
                break
            i += 1

        return False, None, None, start_idx, None, None

    def _format_function_signature(self, tokens, start_idx, end_idx, function_name):
        """
        Format a function signature with special Markdown highlighting.
        """
        signature_tokens = tokens[start_idx:end_idx]
        signature_text = ''.join(token[1] for token in signature_tokens)

        return f"**🔹 {function_name}** {signature_text.strip()}\n"

    def format_unencoded(self, tokensource, outfile):
        """
        Format the token stream and write to outfile.
        """
        # Convert token source to list for multiple passes
        tokens = list(tokensource)

        # Write document header if full document requested
        if self.options.get('full'):
            title = self.options.get('title', 'Code')
            outfile.write(f'# {title}\n\n')
            outfile.write('Generated by Pygments Markdown Formatter\n\n')

        # Pre-process to find function signatures if highlighting is enabled
        function_signatures = []
        if self.highlight_functions:
            i = 0
            while i < len(tokens):
                is_func, func_name, parameters, end_idx, access_modifier, return_type = self._is_function_definition(tokens, i)
                if is_func:
                    # Find the line number for this function
                    line_num = 1
                    char_count = 0
                    for j in range(i):
                        char_count += len(tokens[j][1])
                        line_num += tokens[j][1].count('\n')

                    function_signatures.append({
                        'name': func_name,
                        'parameters': parameters or '',
                        'access_modifier': access_modifier,
                        'return_type': return_type,
                        'start_idx': i,
                        'end_idx': end_idx,
                        'line_num': line_num,
                        'signature': ''.join(token[1] for token in tokens[i:end_idx])
                    })
                    i = end_idx
                else:
                    i += 1

        # Write function signatures summary if any found
        if function_signatures:
            # outfile.write('## 📚 Functions Found\n\n')
            for func in function_signatures:
                # Build the display string with access modifier and return type
                signature_parts = []

                if func['access_modifier']:
                    signature_parts.append(f"{func['access_modifier']}")

                # TODO: we don't currently get all return types so ignore for now
                # if func['return_type']:
                #     signature_parts.append(f"{func['return_type']}")

                # signature_parts.append(f"**{func['name']}**")
                signature_parts.append(f"{func['name']}")

                params_display = f"({func['parameters']})" if func['parameters'] else "()"
                signature_parts.append(params_display)

                signature_display = ' '.join(signature_parts)

                # do we show line numbers?
                if self.linenos:
                    outfile.write(f'- {signature_display} (line {func["line_num"]})\n')
                else:
                    outfile.write(f'{signature_display}\n')

            outfile.write('\n')

        # This entire IF block is to output the entire document in fenced code blocks
        # we will not use this for just getting signatures
        if self.options.get('full'):
            # Start fenced code block
            fence = self.fence_char * self.fence_count
            if self.lang:
                outfile.write(f'{fence}{self.lang}\n')
            else:
                outfile.write(f'{fence}\n')

            # Process tokens line by line
            current_line = []
            line_number = self.linenostart
            token_idx = 0

            while token_idx < len(tokens):
                ttype, value = tokens[token_idx]

                # Check if this is the start of a function signature
                current_func = None
                for func in function_signatures:
                    if token_idx == func['start_idx']:
                        current_func = func
                        break

                # Handle line breaks
                if '\n' in value:
                    parts = value.split('\n')

                    # Process the part before newline
                    if parts[0]:
                        if self.inline_styles:
                            prefix, suffix = self._get_markdown_style(ttype)
                            if prefix or suffix:
                                current_line.append(f'{prefix}{parts[0]}{suffix}')
                            else:
                                current_line.append(parts[0])
                        else:
                            current_line.append(parts[0])

                    # Output the completed line with special function marking
                    self._write_line(outfile, current_line, line_number, tokens, token_idx)
                    line_number += 1
                    current_line = []

                    # Handle multiple newlines
                    for i in range(1, len(parts) - 1):
                        if parts[i]:
                            if self.inline_styles:
                                prefix, suffix = self._get_markdown_style(ttype)
                                if prefix or suffix:
                                    current_line.append(f'{prefix}{parts[i]}{suffix}')
                                else:
                                    current_line.append(parts[i])
                            else:
                                current_line.append(parts[i])
                        self._write_line(outfile, current_line, line_number, tokens, token_idx)
                        line_number += 1
                        current_line = []

                    # Handle the part after the last newline
                    if len(parts) > 1 and parts[-1]:
                        if self.inline_styles:
                            prefix, suffix = self._get_markdown_style(ttype)
                            if prefix or suffix:
                                current_line.append(f'{prefix}{parts[-1]}{suffix}')
                            else:
                                current_line.append(parts[-1])
                        else:
                            current_line.append(parts[-1])
                else:
                    # No newline, just add to current line
                    if value:  # Skip empty values
                        if self.inline_styles:
                            prefix, suffix = self._get_markdown_style(ttype)
                            if prefix or suffix:
                                current_line.append(f'{prefix}{value}{suffix}')
                            else:
                                current_line.append(value)
                        else:
                            current_line.append(value)

                token_idx += 1

            # Output any remaining content
            if current_line:
                self._write_line(outfile, current_line, line_number, tokens, len(tokens) - 1)

            # End fenced code block
            outfile.write(f'{fence}\n')
        else:
            logging.debug('SKIPPED OUTPUTTING FILE CONTENTS - FULL DOCUMENT MODE IS OFF')

        # Add highlighted lines information as comments if specified
        if self.hl_lines:
            outfile.write('\n<!-- Highlighted lines: ')
            outfile.write(', '.join(map(str, sorted(self.hl_lines))))
            outfile.write(' -->\n')

    def _write_line(self, outfile, line_parts, line_number, tokens=None, token_idx=None):
        """
        Write a single line to the output file.
        """
        line_content = ''.join(line_parts)

        # Check if this line contains a function definition for emphasis style
        is_function_line = False
        function_name = ""

        if (self.highlight_functions and tokens and token_idx is not None):
            # Check if current line contains a function definition
            line_tokens = []
            temp_line_num = line_number
            i = max(0, token_idx - 10)  # Look back a bit

            while i <= min(len(tokens) - 1, token_idx + 10):  # Look ahead a bit
                if i < len(tokens):
                    ttype, value = tokens[i]
                    if '\n' in value:
                        if temp_line_num == line_number:
                            line_tokens.append((ttype, value.split('\n')[0]))
                        temp_line_num += value.count('\n')
                        if temp_line_num > line_number:
                            break
                    elif temp_line_num == line_number:
                        line_tokens.append((ttype, value))
                i += 1

            # Check if this line has function keywords
            line_text = ''.join(token[1] for token in line_tokens).strip()
            if any(keyword in line_text for keyword in ['def ', 'function ', 'fn ', 'func ', 'method ', 'proc ', 'procedure ', 'sub ']):
                is_function_line = True
                # Extract function name
                for ttype, value in line_tokens:
                    if ttype in (Name.Function, Name) and value.isidentifier():
                        function_name = value
                        break

        # Add line numbers if requested
        if self.linenos:
            line_prefix = f'{line_number:4d} | '
            outfile.write(line_prefix)

        outfile.write(f'{line_content}\n')

    def get_style_defs(self, arg=None):
        """
        Return style definitions as Markdown comments.
        Since Markdown doesn't have CSS, this returns documentation about
        the inline formatting used.
        """
        if not self.inline_styles:
            return "<!-- No inline styles used -->"

        style_doc = """<!-- Markdown Formatter Style Guide:
- **Bold**: Keywords, headings, important elements
- *Italic*: Comments, preprocessor directives
- ~~Strikethrough~~: Errors, deleted content
- Regular text: Most code elements (strings, names, numbers, operators)
-->"""
        return style_doc


# Register the formatter (this would typically be done in _mapping.py)
__all__ = ['TLDRFormatter']
