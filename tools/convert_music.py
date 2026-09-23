"""Reproduce the pinned LSP assets from the untouched user-selected MOD."""
from pathlib import Path
import argparse
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REVISION = 'fa9c93cd304ead7076e0fce8a1c89d9286d81f9c'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('upstream', type=Path, help='Local checkout of arnaud-carre/LSPlayer')
    args = parser.parse_args()
    upstream = args.upstream.resolve()
    revision = subprocess.check_output(['git', '-C', str(upstream), 'rev-parse', 'HEAD'], text=True).strip()
    if revision != REVISION:
        parser.error(f'Expected upstream revision {REVISION}, got {revision}')
    if subprocess.check_output(['git', '-C', str(upstream), 'status', '--porcelain', '--untracked-files=no']):
        parser.error('Upstream tracked source files must be unmodified')
    output = ROOT/'build/music-conversion'
    output.mkdir(parents=True, exist_ok=True)
    converter = output/'LSPConvert'
    defines = {'strncpy_s':'strncpy','MACOS_LINUX':1,'WINDOWS':0,'_MAX_PATH':260,
               '_MAX_DRIVE':3,'_MAX_DIR':256,'_MAX_FNAME':256,'_MAX_EXT':256,
               'LSP_MAJOR_VERSION':1,'LSP_MINOR_VERSION':31}
    sources = sorted((upstream/'src').glob('*.cpp')) + [upstream/'src/external/micromod/micromod.cpp']
    subprocess.run(['c++','-O2','-std=c++17',*[f'-D{k}={v}' for k,v in defines.items()],
                    *map(str,sources),'-o',str(converter)],check=True)
    music = ROOT/'assets/music'
    data = bytearray((music/'k0w-rsnd.mod').read_bytes())
    assert data[1080:1084] == b'M.K.'
    for i in range(31):
        offset = 20+i*30
        repeat = struct.unpack_from('>H',data,offset+28)[0]
        if not repeat:
            struct.pack_into('>H',data,offset+28,1)
    source = output/'robotsound-normalized.mod'
    source.write_bytes(data)
    subprocess.run([str(converter),str(source),'-fixed50hz',
                    '-lsmusic',str(music/'robotsound.lsmusic'),
                    '-lsbank',str(music/'robotsound.lsbank')],check=True)


if __name__ == '__main__':
    main()
