"""Launch the real ADF on a PAL 68000/OCS Amiga 500, with AROS boot ROM."""
from pathlib import Path
import argparse, os, subprocess, hashlib, shutil

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
p.add_argument('--config-only',action='store_true')
p.add_argument('--rom',help='Optional user-owned Kickstart ROM')
args=p.parse_args()
config=ROOT/'build/Aura Tunnel A500.fs-uae'
data=ROOT/'emulator-data'
data.mkdir(exist_ok=True)
digest=hashlib.sha256((ROOT/'build/demo.bin').read_bytes()).hexdigest()
release=data/'builds'/digest
release.mkdir(parents=True,exist_ok=True)
for name in ('aura-tunnel-amiga.adf','demo.bin','demo.lst','assets.json','scenes.json'):
    shutil.copyfile(ROOT/'build'/name,release/name)
(data/'loaded-build.txt').write_text(str(release)+'\n')
config.write_text(f'''[fs-uae]
amiga_model = A500
chip_memory = 512
slow_memory = 512
fast_memory = 0
floppy_drive_0 = {release/'aura-tunnel-amiga.adf'}
floppy_drive_speed = 100
kickstart_file = {args.rom or 'internal'}
base_dir = {data}
state_dir = {data/'states'}
screenshots_output_dir = {data/'screenshots'}
logs_dir = {data/'logs'}
window_title = Aura Tunnel / Amiga 500 OCS
window_width = 960
window_height = 768
keep_aspect = 1
integer_scaling = 1
fullscreen = 0
automatic_input_grab = 0
uae_cpu_speed = real
uae_cpu_cycle_exact = true
uae_blitter_cycle_exact = true
video_sync = off
keyboard_key_f5 = action_save_state_1
keyboard_key_f6 = action_save_state_2
keyboard_key_f7 = action_screenshot
''')
print(config)
if not args.config_only:
    emulator=os.environ.get('FS_UAE','/Applications/FS-UAE.app/Contents/MacOS/fs-uae')
    subprocess.run([emulator,str(config)],check=True)
