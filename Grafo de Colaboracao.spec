# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\user\\Downloads\\grafo_colaboracao (1)\\lattes_colab\\gui_openalex.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\user\\AppData\\Local\\Programs\\Python\\Python312\\Lib\\site-packages\\pyvis\\templates', 'pyvis/templates'), ('C:\\Users\\user\\AppData\\Local\\Programs\\Python\\Python312\\Lib\\site-packages\\pyvis\\templates\\lib', 'pyvis/templates/lib')],
    hiddenimports=['openalex_colab', 'tkinter', 'networkx', 'community', 'matplotlib', 'matplotlib.backends.backend_tkagg', 'pyvis', 'pyvis.network'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Grafo de Colaboracao',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
