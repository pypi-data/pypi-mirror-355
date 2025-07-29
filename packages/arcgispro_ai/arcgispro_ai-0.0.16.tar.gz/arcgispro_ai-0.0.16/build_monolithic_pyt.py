import os
import re
import sys
import ast
from pathlib import Path

# List of allowed imports (standard library + arcpy + commonly available packages)
ALLOWED_IMPORTS = set([
    'arcpy', 'os', 'sys', 'json', 're', 'math', 'datetime', 'time', 'random', 'collections', 'itertools', 'functools', 'pathlib', 'shutil', 'logging', 'csv', 'copy', 'ast', 'typing', 'traceback', 'subprocess', 'threading', 'concurrent', 'uuid', 'base64', 'hashlib', 'tempfile', 'glob', 'inspect', 'enum', 'warnings', 'contextlib', 'io', 'zipfile', 'struct', 'platform', 'getpass', 'socket', 'http', 'urllib', 'email', 'pprint', 'argparse', 'dataclasses', 'statistics', 'string', 'types', 'site', 'importlib', 'pkgutil', 'codecs', 'signal', 'weakref', 'array', 'bisect', 'heapq', 'queue', 'resource', 'selectors', 'ssl', 'tarfile', 'xml', 'xml.etree', 'xml.dom', 'xml.sax', 'xml.parsers', 'xmlrpc', 'bz2', 'lzma', 'gzip', 'pickle', 'marshal', 'shelve', 'sqlite3', 'ctypes', 'cProfile', 'pstats', 'doctest', 'unittest', 'venv', 'ensurepip', 'distutils', 'site', 'venv', 'wsgiref', 'uuid', 'zoneinfo', 'faulthandler', 'trace', 'token', 'tokenize', 'symtable', 'tabnanny', 'pyclbr', 'py_compile', 'compileall', 'dis', 'formatter', 'gettext', 'locale', 'mailbox', 'mailcap', 'mimetypes', 'mmap', 'msilib', 'netrc', 'nntplib', 'numbers', 'optparse', 'parser', 'pipes', 'poplib', 'profile', 'pydoc', 'quopri', 'reprlib', 'runpy', 'sched', 'secrets', 'selectors', 'smtpd', 'smtplib', 'sndhdr', 'spwd', 'stat', 'sunau', 'symbol', 'symtable', 'sysconfig', 'tabnanny', 'telnetlib', 'termios', 'test', 'textwrap', 'this', 'tkinter', 'turtle', 'tty', 'turtle', 'unittest', 'uu', 'venv', 'webbrowser', 'xdrlib', 'zipapp', 'zlib', 'zoneinfo', 'requests', 'arcgispro_ai', 'core'
])


def extract_imports(source_code):
    """Return a set of imported module names from the given source code."""
    tree = ast.parse(source_code)
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split('.')[0])
    return imports


def inline_code(files):
    seen_imports = set()
    code_blocks = []
    for file in files:
        with open(file, 'r', encoding='utf-8') as f:
            code = f.read()
        # Remove if __name__ == '__main__' blocks (handle indentation)
        code = re.sub(r"^([ \t]*)if __name__ ?== ?['\"]__main__['\"]:.*?(?=^\S|\Z)", '', code, flags=re.DOTALL | re.MULTILINE)
        # Remove module docstrings
        code = re.sub(r'^\s*""".*?"""', '', code, flags=re.DOTALL)
        # Remove duplicate and relative imports
        lines = code.splitlines()
        filtered_lines = []
        for line in lines:
            stripped = line.strip()
            # Remove relative imports
            if stripped.startswith('from .'):
                continue
            if stripped.startswith('import') or stripped.startswith('from'):
                mod = line.split()[1].split('.')[0]
                if mod in seen_imports:
                    continue
                seen_imports.add(mod)
            filtered_lines.append(line)
        filtered = '\n'.join(filtered_lines).strip()
        code_blocks.append(filtered)
    # Join with two newlines to avoid accidental code merging
    return '\n\n'.join(code_blocks)


def check_imports(files):
    """Check for unsupported imports in the given files."""
    unsupported = set()
    for file in files:
        with open(file, 'r', encoding='utf-8') as f:
            code = f.read()
        imports = extract_imports(code)
        for imp in imports:
            if imp not in ALLOWED_IMPORTS:
                unsupported.add(imp)
    return unsupported


def replace_imports_with_inlined_code(toolbox_code: str, util_code: str) -> str:
    lines = toolbox_code.splitlines()
    output_lines = []
    imports_to_replace = [
        'from arcgispro_ai.arcgispro_ai_utils import',
        'from arcgispro_ai.core.api_clients import'
    ]
    util_code_inserted = False
    skip_mode = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        # If the import is inside a parenthesis block, skip lines until the closing parenthesis
        if any(stripped.startswith(pattern) for pattern in imports_to_replace):
            if not util_code_inserted:
                output_lines.append('')
                output_lines.append('# --- INLINED UTILITY CODE ---')
                # Do NOT dedent util_code; preserve original indentation
                output_lines.append(util_code)
                output_lines.append('# --- END INLINED UTILITY CODE ---')
                output_lines.append('')
                util_code_inserted = True
            # If the import is part of a tuple/list, skip until closing parenthesis
            if line.rstrip().endswith('('):
                skip_mode = True
            continue
        if skip_mode:
            # End skip mode when a closing parenthesis is found at the start of a line
            if stripped == ')':
                skip_mode = False
            continue
        output_lines.append(line)
    # Remove consecutive blank lines
    result = '\n'.join(output_lines)
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result


def main():
    """Build a monolithic .pyt file from toolbox and utility modules."""
    root = Path(__file__).parent
    toolbox_file = root / 'arcgispro_ai' / 'toolboxes' / 'arcgispro_ai_tools.pyt'
    util_dir = root / 'arcgispro_ai' / 'toolboxes' / 'arcgispro_ai'  # Utility code
    util_files = [
        util_dir / 'arcgispro_ai_utils.py',
        util_dir / 'core' / 'api_clients.py'
    ]  # Add more as needed

    # Check for unsupported imports
    unsupported = check_imports([toolbox_file] + util_files)
    if unsupported:
        print(f"WARNING: Unsupported imports found: {unsupported}")
    
    # Inline utility code
    util_code = inline_code(util_files)
      # Read the original toolbox file
    with open(toolbox_file, 'r', encoding='utf-8') as f:
        toolbox_code = f.read()
    
    # Debug: Check if GenerateTool is in the original code
    if 'GenerateTool' in toolbox_code:
        print("✓ GenerateTool found in original toolbox file")
    else:
        print("✗ GenerateTool NOT found in original toolbox file")
    
    # Replace imports with inlined code
    result = replace_imports_with_inlined_code(toolbox_code, util_code)
      # Debug: Check if GenerateTool is still in the processed code
    if 'GenerateTool' in result:
        print("✓ GenerateTool preserved after processing")
        # Check if it's in the tools list
        if 'GenerateTool]' in result:
            print("✓ GenerateTool found in tools list")
        else:
            print("✗ GenerateTool NOT found in tools list")
    else:
        print("✗ GenerateTool LOST during processing")
      # Add header comment
    header = '''# -*- coding: utf-8 -*-
"""
arcgispro_ai.pyt - Monolithic Python Toolbox
This file is auto-generated from arcgispro_ai_tools.pyt with inlined dependencies.
Do not edit directly - regenerate using build_monolithic_pyt.py
"""

'''
    
    final_result = header + result
    
    # Debug: Check if GenerateTool is still in the final result
    if 'GenerateTool' in final_result:
        print("✓ GenerateTool present in final result")
    else:
        print("✗ GenerateTool LOST in final result")

    # Write output
    out_file = root / f'arcgispro_ai.pyt'
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(final_result)
    print(f"Monolithic .pyt written to {out_file}")

if __name__ == '__main__':
    main()
