"""Wrap our position-independent boot loader and payload in an 880 KiB ADF."""
from pathlib import Path
import struct, subprocess

root = Path(__file__).resolve().parents[1]
build = root / 'build'
payload = (build / 'demo.bin').read_bytes()
padded = (len(payload) + 511) & ~511
# Payload includes its DMA buffers; the stack is at the allocation's end.
allocation = padded + 4096
assert allocation < 472 * 1024, f'CHIP allocation too large: {allocation}'
music = (build / 'music-score.bin').read_bytes()
music_allocation = (len(music) + 511) & ~511
assert music_allocation <= 512 * 1024
(build / 'size.i').write_text(f'PAYLOAD equ {padded}\nALLOCATION equ {allocation}\nMUSIC_ALLOCATION equ {music_allocation}\n')
subprocess.run([str(root/'bin/vasmm68k_mot'), '-m68000', '-Fbin', '-quiet',
                '-o', 'build/boot.bin', 'src/boot.asm'], cwd=root, check=True)
boot = bytearray((build / 'boot.bin').read_bytes().ljust(1024, b'\0'))
assert len(boot) == 1024
checksum = 0
for value in struct.unpack('>256I', boot):
    checksum += value
    checksum = (checksum & 0xffffffff) + (checksum >> 32)
struct.pack_into('>I', boot, 4, checksum ^ 0xffffffff)
disk = (boot + payload.ljust(padded, b'\0') + music.ljust(music_allocation, b'\0')).ljust(880*1024, b'\0')
(build / 'aura-tunnel-amiga.adf').write_bytes(disk)
print(f'ADF: {len(disk):,} bytes; payload {len(payload):,}; CHIP allocation {allocation:,}')
