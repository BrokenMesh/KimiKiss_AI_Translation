#!/usr/bin/env python3
"""Apply the QA settings to a PCSX2.ini that PCSX2 generated itself.

Usage: pcsx2_configure.py <PCSX2.ini> <bios_dir> <bios_file>

A hand-written ini is rejected ("Settings failed to load"), so first let
PCSX2 create its default ini (run it once in portable mode), then patch it:
no setup wizard or shutdown prompt, PINE on slot 28011, fast boot, software
renderer, null audio (the container has no sound device; Cubeb pops a modal
error), and the given BIOS.
"""
import sys

SETTINGS = {
    'UI': {'SetupWizardIncomplete': 'false', 'ConfirmShutdown': 'false'},
    'EmuCore': {'EnablePINE': 'true', 'PINESlot': '28011', 'EnableFastBoot': 'true'},
    'EmuCore/GS': {'Renderer': '13'},
    'SPU2/Output': {'Backend': 'Null'},
}


def main():
    path, bios_dir, bios_file = sys.argv[1:4]
    wanted = {s: dict(kv) for s, kv in SETTINGS.items()}
    wanted.setdefault('Folders', {})['Bios'] = bios_dir
    wanted.setdefault('Filenames', {})['BIOS'] = bios_file
    lines = open(path, encoding='utf-8').read().splitlines()
    out, section, done = [], None, set()
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('[') and stripped.endswith(']'):
            for key, value in wanted.get(section, {}).items():
                if (section, key) not in done:
                    out.append(f'{key} = {value}')
                    done.add((section, key))
            section = stripped[1:-1]
        elif '=' in line and section in wanted:
            key = line.split('=', 1)[0].strip()
            if key in wanted[section]:
                line = f'{key} = {wanted[section][key]}'
                done.add((section, key))
        out.append(line)
    for key, value in wanted.get(section, {}).items():
        if (section, key) not in done:
            out.append(f'{key} = {value}')
            done.add((section, key))
    missing = {(s, k) for s, kv in wanted.items() for k in kv} - done
    if missing:
        sys.exit(f'sections not found in {path}: {sorted(missing)}')
    open(path, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    print(f'patched {len(done)} settings in {path}')


if __name__ == '__main__':
    main()
