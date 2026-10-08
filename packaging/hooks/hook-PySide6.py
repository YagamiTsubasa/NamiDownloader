# Collect wheel files statically: importing Qt during build requires CPU sysctls
# unavailable in restricted build environments. Runtime Qt is unchanged.
from pathlib import Path
from PyInstaller.utils.hooks import get_package_paths
root = Path(get_package_paths('PySide6')[1])
hiddenimports = ['shiboken6', 'inspect', 'PySide6.support.deprecated']
binaries = []
for group in ('platforms', 'imageformats', 'iconengines', 'styles', 'tls', 'networkinformation'):
    for p in (root / 'Qt/plugins' / group).glob('*.dylib'):
        if p.name == 'libqpdf.dylib':
            continue  # QtPdf is an unused optional Addons component.
        binaries.append((str(p), 'PySide6/Qt/plugins/' + group))
datas = [(str(root / 'Qt/translations'), 'PySide6/Qt/translations')]
