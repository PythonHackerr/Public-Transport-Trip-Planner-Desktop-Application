block_cipher = None
a = Analysis(['main.py'],
         pathex=[],
         binaries=None,
         datas=[("Assets/*", "Assets")],
         hiddenimports=['cryptography.hazmat.primitives.kdf.pbkdf2'],  # oracle db issues
         hookspath=None,
         runtime_hooks=None,
         excludes=['PySide6.QtQuick', 'PySide6.QtQuickWidgets'],
         cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
         cipher=block_cipher)

Key = ['3D', 'mkl', 'Translation']

def remove_from_list(input, keys):
    outlist = []
    for item in input:
        name, _, _ = item
        flag = 0
        for key_word in keys:
            if name.find(key_word) > -1:
                flag = 1
        if flag != 1:
            outlist.append(item)
    return outlist

a.binaries = remove_from_list(a.binaries, Key)

exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='Pa jak podjade',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='app',
               onefile=True)