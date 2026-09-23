"""Check live animated-background banks, or the runner's borrowed sunset cache."""
from pathlib import Path
import json
import re
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from read_snapshot import inspect
from roto_codec import decode
from roto_background import decode as decode_background, half_turn

result,saved=inspect(ROOT/'emulator-data/states/Saved State 1.uss')
release=Path((ROOT/'emulator-data/loaded-build.txt').read_text().strip())
binary=(release/'demo.bin').read_bytes();listing=(release/'demo.lst').read_text()
symbol=lambda name:int(re.search(r'^'+name+r'\s+[AE]:([0-9A-Fa-f]+)$',listing,re.M)[1],16)
manifest=json.loads((release/'assets.json').read_text())
def asset(name):
    entry=manifest[name];start=symbol('assets')+entry['offset']
    return binary[start:start+entry['size']]
memory=saved['CRAM'];state=result['state']
u16=lambda address:struct.unpack_from('>H',memory,address)[0]
u32=lambda address:struct.unpack_from('>I',memory,address)[0]
field=lambda name:u32(state+symbol(name))
copper=field('COP')
pointer=lambda plane:(u16(copper+plane*8+2)<<16)|u16(copper+plane*8+6)
if result['scene']==2:
    assert u16(state+symbol('ROTOARTREADY'))==1
    front,back=field('ROTOBGFRONT'),field('ROTOBGBACK')
    assert {front,back}=={field('OLD'),field('OLD')+symbol('PLANE')}
    pose=u16(state+symbol('ROTOBGPOSE'))
    index=struct.unpack('>'+str(len(asset('ROTO_BG_INDEX'))//4)+'I',asset('ROTO_BG_INDEX'))
    def background(p):
        phase=p%(len(index)-1)
        raw=decode_background(asset('ROTO_BG_PACKED')[index[phase]:index[phase+1]],symbol('ROTO_BG_BYTES'))
        return half_turn(raw) if p>=len(index)-1 else raw
    raw=background(pose)
    image=bytes(symbol('ROTO_BG_OFFSET'))+raw
    image+=bytes(symbol('PLANE')-len(image))
    assert memory[front:front+len(image)]==image,'Rotating background cache'
    assert pointer(1) in (front,back),'Even-plane DMA reads outside background banks'
    # A snapshot can land before publication; inspect the actual displayed bank.
    displayed=memory[pointer(1)+symbol('ROTO_BG_OFFSET'):pointer(1)+symbol('ROTO_BG_OFFSET')+len(raw)]
    matches=[p for p in range(symbol('ROTO_BG_PHASES')) if background(p)==displayed]
    assert len(matches)==1,'Display scans an incomplete rotation pose'
    foreground_pose=u16(state+symbol('ROPOSE'))
    foreground_index=struct.unpack('>65I',asset('ROTO_INDEX'))
    foreground=decode(asset('ROTO_COMPRESSED')[foreground_index[foreground_pose]:foreground_index[foreground_pose+1]],3200)
    assert memory[field('ROFRONT'):field('ROFRONT')+len(foreground)]==foreground
    result.update(background_pose=pose,displayed_pose=matches[0],front=front,back=back,
                  background_bytes_verified=len(image),foreground_pose=foreground_pose,
                  foreground_bytes_verified=len(foreground))
elif result['scene']==6:
    assert u16(state+symbol('SUNSETREADY'))==1
    low=decode(asset('SUNSET_LOW'),symbol('SCREEN'))
    high=decode(asset('SUNSET_HIGH'),symbol('PLANE'))
    assert memory[field('OLD'):field('OLD')+len(low)]==low
    assert memory[field('MASKBUF'):field('MASKBUF')+len(high)]==high
    assert [pointer(i) for i in range(3)]==[field('OLD'),field('OLD')+symbol('PLANE'),field('MASKBUF')]
    bodies=u16(state+symbol('BODIES'))
    assert u16(field('COPMODE')+2)==(0x5200 if bodies else 0x4200)
    result.update(bodies=bool(bodies),sunset_bytes_verified=len(low)+len(high))
else:
    raise AssertionError('Select roto (3) or runner (7), then save with F5')
path=ROOT/'validation/roto-motion-native.json'
history=json.loads(path.read_text()) if path.exists() else []
history.append(result)
path.write_text(json.dumps(history,indent=2)+'\n')
print(json.dumps(result,indent=2))
