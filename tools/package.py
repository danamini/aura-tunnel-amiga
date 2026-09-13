"""Package the bootable development preview with its provenance and notices."""
from pathlib import Path
import hashlib
import json
import shutil

root = Path(__file__).resolve().parents[1]
build = root / 'build'
dest = root / 'dist'
dest.mkdir(exist_ok=True)
disk = build / 'aura-tunnel-amiga.adf'
binary = (build / 'demo.bin').read_bytes()
shutil.copyfile(disk, dest / disk.name)

# Only normalize presentation whitespace; retain every notice's text and source.
notice_sources = [
    'CREDITS.md', 'LICENSE', 'assets/reference/LICENSE',
    'assets/fighters/SOURCE.md', 'assets/reference/assets/mocap/SOURCE.md',
    'assets/reference/assets/mocap/READMEFIRST.txt',
]
notices = []
for name in notice_sources:
    text = '\n'.join(line.expandtabs().rstrip()
                     for line in (root / name).read_text().splitlines()).rstrip()
    notices.append(name + '\n' + text)
(dest / 'NOTICE.txt').write_text('\n\n'.join(notices) + '\n')

allocation = ((len(binary) + 511) & ~511) + 4096
scenes = json.loads((build / 'scenes.json').read_text())
metadata = {
    'status': 'development preview',
    'platform': 'Amiga 500 / PAL / OCS / 68000',
    'memory': '512 KiB CHIP + 512 KiB slow; no fast RAM',
    'spectrum_source': 'https://github.com/danamini/aura-tunnel',
    'disk_sha256': hashlib.sha256(disk.read_bytes()).hexdigest(),
    'binary_sha256': hashlib.sha256(binary).hexdigest(),
    'payload_bytes': len(binary),
    'chip_allocation_bytes': allocation,
    'scene_cycle_seconds': sum(scene['ticks'] for scene in scenes) / 50,
    'limitations': 'See docs/implementation-plan.md; this preview is not a finished release.',
}
(dest / 'build-info.json').write_text(json.dumps(metadata, indent=2) + '\n')
print(dest / disk.name)
