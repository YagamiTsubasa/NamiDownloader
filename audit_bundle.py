"""Reject native libraries accidentally depending on the builder's Homebrew paths."""
from pathlib import Path
import subprocess
import sys
bad = []
for path in Path(sys.argv[1]).rglob('*'):
    if not path.is_file() or path.is_symlink(): continue
    result = subprocess.run(['file', '-b', str(path)], capture_output=True, text=True)
    if 'Mach-O' not in result.stdout: continue
    links = subprocess.check_output(['otool', '-L', str(path)], text=True)
    for line in links.splitlines()[1:]:
        dep = line.strip().split(' (')[0]
        if dep.startswith('/') and not dep.startswith(('/usr/lib/', '/System/Library/')):
            bad.append(f'{path}: {dep}')
if bad:
    raise SystemExit('应用仍依赖构建机外部库，禁止分发：\n' + '\n'.join(bad))
print('Native dependency path audit passed.')
