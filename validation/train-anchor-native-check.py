"""Check rendered carriage pixels and live DMA fighter roots in the same frame."""
from pathlib import Path
import json,re,struct,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from read_snapshot import inspect
from roto_codec import decode
result,saved=inspect(ROOT/'emulator-data/states/Saved State 1.uss')
assert result['scene']==9,'Select 0, pause with Space, then save F5'
release=Path((ROOT/'emulator-data/loaded-build.txt').read_text().strip())
binary=(release/'demo.bin').read_bytes();listing=(release/'demo.lst').read_text()
symbol=lambda name:int(re.search(r'^'+name+r'\s+[AE]:([0-9A-Fa-f]+)$',listing,re.M)[1],16)
manifest=json.loads((release/'assets.json').read_text())
def asset(name):
    entry=manifest[name];start=symbol('assets')+entry['offset']
    return binary[start:start+entry['size']]
memory=saved['CRAM'];state=result['state']
u16=lambda a:struct.unpack_from('>H',memory,a)[0]
u32=lambda a:struct.unpack_from('>I',memory,a)[0]
field=lambda name:u32(state+symbol(name))
assert u16(state+symbol('TRAINART'))==1
frame=result['scene_frame'];travel=frame>>symbol('TRAIN_TRAVEL_SHIFT')
shake=struct.unpack_from('>h',binary,symbol('train_shake')+((frame>>2)&15)*2)[0]
roof=symbol('TRAIN_ROOF_Y')+shake
car=decode(asset('TRAIN_ART1'),9984)
row=car[20*96:21*96]
source=''.join(f'{v:08b}' for v in row)[travel:travel+320]
expected=int(source,2).to_bytes(40,'big')
front=field('FRONT')
assert memory[front+(roof+20)*40:front+(roof+21)*40]==expected,'Carriage displacement differs from shared travel'
assert memory[front+roof*40:front+(roof+1)*40]==b'\xff'*40,'Deck not at carriage roof'
fighters=[]
for side,anchor in enumerate(('TRAIN_LEFT_ANCHOR','TRAIN_RIGHT_ANCHOR')):
    roots=[];bottoms=[]
    for segment in range(3):
        cp=field('COPSPR')+(side*4+segment)*8
        ptr=(u16(cp+2)<<16)|u16(cp+6)
        raw=memory[ptr:ptr+232]
        x=(raw[1]<<1)|(raw[3]&1)
        roots.append(x-segment*16)
        occupied=[y for y in range(56) if any(raw[4+y*4:8+y*4])]
        if occupied:bottoms.append(raw[0]-44+max(occupied))
    assert roots==[symbol(anchor)-travel]*3,'Fighter slides relative to carriage'
    assert max(bottoms)==roof-1,'Feet float above or penetrate roof'
    fighters.append({'screen_x':roots[0]-129,'foot_y':max(bottoms),'roof_relative_x':roots[0]-129+travel})
result.update(carriage_travel=travel,roof_y=roof,fighters=fighters,carriage_row_bytes_verified=40)
path=ROOT/'validation/train-anchor-native.json'
history=json.loads(path.read_text()) if path.exists() else []
history.append(result);path.write_text(json.dumps(history,indent=2)+'\n')
print(json.dumps(result,indent=2))
