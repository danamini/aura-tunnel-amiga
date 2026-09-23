"""Compare the live solid cache and colour bands with the launched disk assets."""
from pathlib import Path
import json,re,struct,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from read_snapshot import inspect
from roto_codec import decode
result,saved=inspect(ROOT/'emulator-data/states/Saved State 1.uss')
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
if result['scene']==5:
    pose=u16(state+symbol('CUBEPOSE'))
    index=struct.unpack('>'+str(len(asset('SOLID_INDEX'))//4)+'I',asset('SOLID_INDEX'))
    assert 0<=pose<symbol('SOLID_FRAMES')
    raw=bytearray();cache_addresses=[field('OLD'),field('MASKBUF'),result['base']+symbol('hires_a'),result['base']+symbol('roto_a'),result['base']+symbol('hires_a')+10240]
    banks_verified=0
    for family,(offset,height,width,plane) in enumerate(struct.iter_unpack('>HHHH',asset('SOLID_LAYOUT'))):
        bank=decode(asset('SOLID_PACKED')[index[family]:index[family+1]],plane*2*symbol('SOLID_FRAMES'))
        address=cache_addresses[family]
        assert memory[address:address+len(bank)]==bank, f'Solid bank {family}'
        banks_verified+=len(bank)
        frame=bank[pose*plane*2:(pose+1)*plane*2]
        raw.extend(frame)
        raw.extend(bytes(a|b for a,b in zip(frame[:plane],frame[plane:])))
    assert memory[field('GRAPHBUF'):field('GRAPHBUF')+len(raw)]==raw,'Native solids or silhouette differ'
    palette=list(struct.iter_unpack('>HHH',asset('SOLID_COLOURS')))
    bands=[]
    for band in range(8,48):
        address=u32(field('COPINDEX')+band*4)
        colours=tuple(u16(address+offset) for offset in (10,14,18))
        assert colours in palette,'Unexpected solid palette'
        bands.append(colours)
    assert len(set(bands))>20,'Missing colour reflections'
    result.update(solid_pose=pose,solid_bytes_verified=len(raw),banks_bytes_verified=banks_verified,distinct_colour_bands=len(set(bands)))
elif result['scene']==0:
    raw=decode(asset('BRIEF_PACKED'),5760)
    assert memory[field('HIWORK'):field('HIWORK')+len(raw)]==raw,'Briefing cache'
    result.update(briefing_bytes_verified=len(raw))
else:raise AssertionError('Select 6 (solids) or 1 (briefing), pause and save with F5')
path=ROOT/'validation/solid-shapes-native.json'
history=json.loads(path.read_text()) if path.exists() else []
history.append(result);path.write_text(json.dumps(history,indent=2)+'\n')
print(json.dumps(result,indent=2))
