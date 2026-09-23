"""Compare the emulator's mutable font cache with decoded angle assets."""
from pathlib import Path
import sys,json,re,struct,hashlib
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'tools'))
from read_snapshot import inspect
from roto_codec import decode
from big_spins import POSE_BYTES
result,saved=inspect(root/'emulator-data/states/Saved State 1.uss')
assert result['sha256']==hashlib.sha256((root/'build/demo.bin').read_bytes()).hexdigest(),'Rebuild changed native addresses/assets'
assert result['scene']==4,'Save state must be in big sine scene'
memory=saved['CRAM'];state=result['state']
u32=lambda off:struct.unpack_from('>I',memory,state+off)[0]
assets=(root/'build/assets.bin').read_bytes();manifest=json.loads((root/'build/assets.json').read_text())
def asset(name):
    a=manifest[name];return assets[a['offset']:a['offset']+a['size']]
constants=dict(re.findall(r'^(\w+) equ (\d+)$',(root/'build/assets.i').read_text(),re.M))
stride=int(constants['HI_STRIDE']);width=int(constants['HIWIDTH'])
expected=bytearray((root/'build/hi-bitmap-raw.bin').read_bytes())
angles=memory[state+212:state+212+len(asset('BIG_SPIN_MAP'))]
index=struct.unpack('>'+str(len(asset('BIG_SPIN_INDEX'))//4)+'I',asset('BIG_SPIN_INDEX'));packed=asset('BIG_SPIN_PACKED')
for char,(family,angle) in enumerate(zip(asset('BIG_SPIN_MAP'),angles)):
    if family==255 or angle==0:continue
    pose=family*16+angle;raw=decode(packed[index[pose]:index[pose+1]],POSE_BYTES)
    for row in range(40):
        expected[row*stride+char*16:row*stride+char*16+16]=raw[row*16:row*16+16]
for row in range(40):expected[row*stride+width//8:(row+1)*stride]=expected[row*stride:row*stride+82]
assert any(angles),'Must capture an active rotating pose'
assert memory[u32(8):u32(8)+len(expected)]==expected,'Native rotation cache differs from expected'
stretch=decode(asset('HI_STRETCH_PACKED'),int(constants['HI_STRETCH_SIZE']))
stretch_address=u32(72)+int(constants['HI_STRETCH_CACHE'])
assert memory[stretch_address:stretch_address+len(stretch)]==stretch,'Wave mask overwrote stretch cache'
result['rotating_angles']=list(angles);result['font_bytes_verified']=len(expected)
result['stretch_bytes_verified']=len(stretch)
(root/'validation/hires-big-spin-native.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS native spinning font and wrapped seam:',len(expected),'bytes; angles',list(angles))
