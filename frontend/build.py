#!/usr/bin/env python3
"""
Assemble frontend/index.html from shell + page fragments + app.js.

Usage:
    python frontend/build.py          # assemble and write index.html
    python frontend/build.py --check  # print what would change, don't write

Structure:
    frontend/shell.html       — head, navbar, sidebar, main wrapper skeleton
    frontend/pages/*.html     — one file per page (includes the outer x-show div)
    frontend/js/app.js        — Alpine app() function and all state/methods
    frontend/index.html       — assembled output (served by FastAPI)
"""

import sys
from pathlib import Path

HERE = Path(__file__).parent

PAGES = [
    'home',
    'recommendations',
    'all_stocks',
    'per_stock',
    'comparison',
    'portfolio',
    'trades',
    'mf',
    'lenses',
    'watchlist',
]


def assemble() -> str:
    shell = (HERE / 'shell.html').read_text()
    pages_html = '\n'.join(
        (HERE / 'pages' / f'{p}.html').read_text() for p in PAGES
    )
    app_js = (HERE / 'js' / 'app.js').read_text()

    result = shell.replace('<!-- PAGES_PLACEHOLDER -->', pages_html)
    result = result.replace('// APP_JS_PLACEHOLDER', app_js)
    return result


def main():
    check_only = '--check' in sys.argv
    output = assemble()
    out_path = HERE / 'index.html'

    if check_only:
        current = out_path.read_text() if out_path.exists() else ''
        if current == output:
            print('index.html is up to date.')
        else:
            print('index.html is OUT OF DATE — run build.py to update.')
        return

    out_path.write_text(output)
    total = sum((HERE / 'pages' / f'{p}.html').stat().st_size for p in PAGES)
    js_size = (HERE / 'js' / 'app.js').stat().st_size
    print(f'Built index.html  ({len(output.splitlines())} lines)')
    print(f'  pages: {total // 1024}KB across {len(PAGES)} files')
    print(f'  app.js: {js_size // 1024}KB')


if __name__ == '__main__':
    main()
