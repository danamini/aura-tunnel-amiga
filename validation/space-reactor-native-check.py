"""Verify the decoded space scene and reactor cache in a real FS-UAE snapshot."""
from pathlib import Path
import json
import re
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from read_snapshot import inspect
from roto_codec import decode

result,saved=inspect(ROOT/'emulator-data/states/Saved State 1.uss')
assert result['scene']==7,'Select Deep Space (8), then save with F5'
release=Path((ROOT/'emulator-data/loaded-build.txt').read_text().strip())
binary=(release/'demo.bin').read_bytes()
listing=(release/'demo.lst').read_text()
symbol=lambda name:int(re.search(r'^'+name+r'\s+[AE]:([0-9A-Fa-f]+)$',listing,re.M)[1],16)
manifest=json.loads((release/'assets.json').read_text())
def asset(name):
    entry=manifest[name];start=symbol('assets')+entry['offset']
    return binary[start:start+entry['size']]
memory=saved['CRAM'];state=result['state']
u16=lambda address:struct.unpack_from('>H',memory,address)[0]
u32=lambda address:struct.unpack_from('>I',memory,address)[0]
assert u16(state+symbol('SPACEREADY'))==1
background=decode(asset('SPACE_BACKGROUND_PACKED'),symbol('SCREEN'))
background_address=u32(state+symbol('OLD'))
assert memory[background_address:background_address+len(background)]==background
pose=u16(state+symbol('SPACEPOSE'))
index=struct.unpack('>'+str(len(asset('REACTOR_INDEX'))//4)+'I',asset('REACTOR_INDEX'))
assert 0<=pose<symbol('REACTOR_FRAMES')
raw=decode(asset('REACTOR_PACKED')[index[pose]:index[pose+1]],symbol('REACTOR_POSE_BYTES'))
plane=symbol('REACTOR_PLANE_BYTES')
mask=bytes(a|b for a,b in zip(raw[:plane],raw[plane:]))
cache=u32(state+symbol('GRAPHBUF'))
assert memory[cache:cache+len(raw)+len(mask)]==raw+mask,'Native reactor/mask differs'
copper=u32(state+symbol('COP'))
for n in range(2):
    pointer=(u16(copper+n*8+2)<<16)|u16(copper+n*8+6)
    assert pointer==background_address+n*symbol('PLANE'),'Background DMA pointer'
result.update(reactor_pose=pose,reactor_bytes_verified=len(raw)+len(mask),
              background_bytes_verified=len(background))
path=ROOT/'validation/space-reactor-native.json'
history=json.loads(path.read_text()) if path.exists() else []
history.append(result)
path.write_text(json.dumps(history,indent=2)+'\n')
print(json.dumps(result,indent=2))
