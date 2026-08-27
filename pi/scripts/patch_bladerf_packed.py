#!/usr/bin/env python3
"""Patch bladerf Python bindings to add SC16_Q11_PACKED format support.

Run once on the Pi (with sudo if bladerf is installed system-wide):
    sudo python3 patch_bladerf_packed.py

This adds BLADERF_FORMAT_SC16_Q11_PACKED (value=1) to the cffi enum
and SC16_Q11_PACKED to the Python Format class, enabling 12-bit packed
IQ transfer over USB (33% bandwidth savings, no data quality loss).
"""

import importlib
import os
import sys

def find_bladerf_path():
    import bladerf
    return os.path.dirname(bladerf.__file__)

def patch_cdef(bladerf_dir):
    path = os.path.join(bladerf_dir, '_cdef.py')
    with open(path, 'r') as f:
        content = f.read()

    if 'BLADERF_FORMAT_SC16_Q11_PACKED' in content:
        print(f"[OK] _cdef.py already patched")
        return False

    old = 'BLADERF_FORMAT_SC16_Q11 = 0,'
    new = 'BLADERF_FORMAT_SC16_Q11 = 0,\n    BLADERF_FORMAT_SC16_Q11_PACKED = 1,'

    if old not in content:
        print(f"[ERROR] Cannot find '{old}' in {path}")
        sys.exit(1)

    content = content.replace(old, new)
    with open(path, 'w') as f:
        f.write(content)
    print(f"[PATCHED] {path}")
    return True

def patch_bladerf_py(bladerf_dir):
    path = os.path.join(bladerf_dir, '_bladerf.py')
    with open(path, 'r') as f:
        content = f.read()

    if 'SC16_Q11_PACKED' in content:
        print(f"[OK] _bladerf.py already patched")
        return False

    old = 'SC16_Q11 = libbladeRF.BLADERF_FORMAT_SC16_Q11'
    new = ('SC16_Q11 = libbladeRF.BLADERF_FORMAT_SC16_Q11\n'
           '    SC16_Q11_PACKED = libbladeRF.BLADERF_FORMAT_SC16_Q11_PACKED')

    if old not in content:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'SC16_Q11' in line and 'class' not in line and 'PACKED' not in line and 'META' not in line:
                indent = len(line) - len(line.lstrip())
                spaces = ' ' * indent
                lines.insert(i + 1, f'{spaces}SC16_Q11_PACKED = libbladeRF.BLADERF_FORMAT_SC16_Q11_PACKED')
                content = '\n'.join(lines)
                break
        else:
            print(f"[ERROR] Cannot find SC16_Q11 enum entry in {path}")
            sys.exit(1)
    else:
        content = content.replace(old, new)

    with open(path, 'w') as f:
        f.write(content)
    print(f"[PATCHED] {path}")
    return True

def verify():
    import importlib
    import bladerf._cdef
    import bladerf._bladerf
    importlib.reload(bladerf._cdef)
    importlib.reload(bladerf._bladerf)
    from bladerf._bladerf import Format
    val = Format.SC16_Q11_PACKED
    print(f"[VERIFY] Format.SC16_Q11_PACKED = {val}")

if __name__ == '__main__':
    bladerf_dir = find_bladerf_path()
    print(f"bladerf package: {bladerf_dir}")

    patched = False
    patched |= patch_cdef(bladerf_dir)
    patched |= patch_bladerf_py(bladerf_dir)

    if patched:
        print("\nVerifying...")
        verify()
        print("\nDone! Restart any running bladerf processes.")
    else:
        print("\nAlready patched, nothing to do.")
