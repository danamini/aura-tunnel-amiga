"""Keep a bootable development preview with the parked source revision."""
from pathlib import Path
import hashlib,json,shutil,struct

root=Path(__file__).resolve().parents[1];build=root/'build';dest=root/'dist'
dest.mkdir(exist_ok=True)
disk=build/'aura-tunnel-amiga.adf';binary=(build/'demo.bin').read_bytes()
shutil.copyfile(disk,dest/disk.name)
# Keep redistribution notices beside the standalone disk, not just in source.
notice_sources=['CREDITS.md','LICENSE','assets/reference/LICENSE',
                'assets/fighters/SOURCE.md','assets/reference/assets/mocap/SOURCE.md',
                'assets/reference/assets/mocap/READMEFIRST.txt']
(dest/'NOTICE.txt').write_text('\n\n'.join(name+'\n'+(root/name).read_text() for name in notice_sources)+'\n')
allocation=((len(binary)+511)&~511)+4096
metadata={'status':'parked development preview','platform':'Amiga 500 / PAL / OCS / 68000',
 'memory':'512 KiB CHIP + 512 KiB slow; no fast RAM','spectrum_source':'https://github.com/danamini/aura-tunnel',
 'disk_sha256':hashlib.sha256(disk.read_bytes()).hexdigest(),
 'binary_sha256':hashlib.sha256(binary).hexdigest(),
 'payload_bytes':len(binary),'chip_allocation_bytes':allocation,
 'scene_cycle_seconds':sum(s['ticks'] for s in json.loads((build/'scenes.json').read_text()))/50,
 'limitations':'See docs/implementation-plan.md; this preview is not a finished release.'}
(dest/'build-info.json').write_text(json.dumps(metadata,indent=2)+'\n')
print(dest/disk.name)
