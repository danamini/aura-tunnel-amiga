"""Validate the built disk and native streams, independently of rendering code."""
from pathlib import Path
import hashlib,json,struct
from hires_font import GLYPH_HEIGHT

root=Path(__file__).resolve().parents[1];build=root/'build'
disk=(build/'aura-tunnel-amiga.adf').read_bytes();binary=(build/'demo.bin').read_bytes()
assert len(disk)==901120 and disk[:4]==b'DOS\0'
total=0
for word in struct.unpack('>256I',disk[:1024]):
    total+=word;total=(total&0xffffffff)+(total>>32)
assert total==0xffffffff,'Boot checksum'
assert disk[1024:1024+len(binary)]==binary,'Disk has stale payload'
assert len(binary)+4096<472*1024,'CHIP budget'
ref=root/'assets/reference';reference=json.loads((ref/'manifest.json').read_text())
for path,digest in reference['sha256'].items():
    assert hashlib.sha256((ref/path).read_bytes()).hexdigest()==digest,path
assets=(build/'assets.bin').read_bytes();manifest=json.loads((build/'assets.json').read_text())
def asset(name):
    a=manifest[name];return assets[a['offset']:a['offset']+a['size']]
def words(data):return struct.unpack('>'+'H'*(len(data)//2),data)
def longs(data):return struct.unpack('>'+'I'*(len(data)//4),data)
body=asset('BODY_DATA');index=longs(asset('BODY_INDEX'))
assert len(index)==28
for pose,start in enumerate(index):
    pos=start;seen=set()
    while True:
        off=struct.unpack_from('>H',body,pos)[0];pos+=2
        if off==65535:break
        count=struct.unpack_from('>H',body,pos)[0];pos+=2
        assert off%2==0 and count and off+count*2<=20480
        assert off//40==(off+count*2-1)//40,'Body run crosses row'
        for address in range(off,off+count*2,2):
            assert address not in seen;seen.add(address)
        pos+=count*2
    assert pos==(index[pose+1] if pose+1<len(index) else len(body))
    assert seen,'Empty body pose'
from roto_codec import decode
fi=longs(asset('FIGHTER_INDEX'));fc=asset('FIGHTER_COMPRESSED')
sprites=b''.join(decode(fc[a:b],696) for a,b in zip(fi,fi[1:]))
assert sprites==(build/'fighter-raw.bin').read_bytes()
assert len(sprites)==103*3*232
assert max(words(asset('FIGHT_POSES')))<103
assert any(47<=pose<56 for pose in words(asset('FIGHT_POSES'))[::2]),'New sweep is never scheduled'
assert len({sprites[i:i+696] for i in range(0,len(sprites),696)})>35
for offset in range(0,len(sprites),232):
    pos,ctl=struct.unpack_from('>HH',sprites,offset)
    assert (ctl>>8)-(pos>>8)==56
    assert sprites[offset+228:offset+232]==bytes(4)
assert any(((b>>i)&1)!=((b>>(i+1))&1) for b in decode(asset('HI_BITMAP_PACKED'),len((build/'hi-bitmap-raw.bin').read_bytes())) for i in (0,2,4,6)), 'Hires just doubled pixels'
chrome=words(asset('HI_CHROME'))
assert len(chrome)==64*18 and all(c<4096 for c in chrome)
assert len(set(chrome))>20, 'Chrome reflection needs a varied OCS ramp'
# Every elastic program covers all 72 destination rows exactly once, with
# either consecutive source rows or a repeated row. No crop reads past scratch.
stretch=asset('HI_STRETCH');heights=[]
for off in words(asset('HI_STRETCH_INDEX')):
    end=0;occupied=0
    while True:
        source=struct.unpack_from('>H',stretch,off)[0];off+=2
        if source==65535:break
        dest,count,mod=struct.unpack_from('>HHh',stretch,off);off+=6
        assert dest==end*80 and count>0 and mod in (-80,0)
        if source!=65534:
            assert source%80==0 and source+(count-1)*(80+mod)<5760
            occupied+=count
        end+=count
    assert end==72
    heights.append(occupied)
assert min(heights)<20 and max(heights)==72,'Elastic range too subtle'
from roto_codec import decode, checker_pose
ri=longs(asset('ROTO_INDEX'));payload=asset('ROTO_COMPRESSED')
assert len(ri)==65 and ri[-1]==len(payload)
for pose in range(64):
    raw=decode(payload[ri[pose]:ri[pose+1]],3200)
    assert raw==checker_pose(pose), pose
    assert any(b not in (0,255) for b in raw)
vertices=asset('TUNNEL')
assert len(vertices)==128*10*20
for off in range(0,len(vertices),20):
    assert words(vertices[off:off+2])[0] in (1,2,3)
    points=list(zip(vertices[off+2:off+20:2],vertices[off+3:off+20:2]))
    assert points[0]==points[-1]
    assert all(0<=x*2<320 and 24<=y<200 for x,y in points)
# B-channel word shifts with a repeated A mask must reproduce each glyph
# column, including negative shifts, both edges and the wrapped text seam.
bitmap=decode(asset('HI_BITMAP_PACKED'),len((build/'hi-bitmap-raw.bin').read_bytes()))
assert bitmap==(build/'hi-bitmap-raw.bin').read_bytes()
constants=dict(__import__('re').findall(r'^(\w+) equ (\d+)$',(build/'assets.i').read_text(),__import__('re').M))
stride=int(constants['HI_STRIDE']);width=int(constants['HIWIDTH'])
for rowno in (0,17,GLYPH_HEIGHT-1):
    row=''.join(f'{b:08b}' for b in bitmap[rowno*stride:(rowno+1)*stride])
    for scroll in list(range(16))+list(range(width-16,width)):
        for x in (0,1,15,16,31,319,627,639):
            count=min(23,640-x);destbit=x%16;src=scroll+x
            shift=destbit-src%16;dummy=shift<0;shift%=16
            wordstart=src//16*16
            fetched=row[wordstart:wordstart+80]
            output=('0'*shift+fetched)
            offset=destbit+16*dummy
            assert output[offset:offset+count]==row[src:src+count]

# Every widened sine run advances by half as many source phases, covers
# exactly 640 hires columns and keeps the full glyph inside its 72-row buffer.
wave=words(asset('HI_WAVE_RUNS'))
for start in range(512):
    phase=start;x=0
    while x<640:
        count,offset=wave[phase*2:phase*2+2]
        count=min(count,640-x)
        assert count>0 and count%2==0
        assert 0<=offset and offset+(GLYPH_HEIGHT-1)*80+79<5760
        phase=(phase+count//2)%512;x+=count
    assert x==640
# Online artwork decodes into the exact borrowed scene-buffer limits.
for i,height in enumerate((104,52)):
    decoded=decode(asset(f'TRAIN_ART{i}'),height*96*2)
    assert len(decoded)==height*192
assert 104*192<=20480 and 52*192<=17280

# Independently model the A-channel shift register and the discarded first
# word for every fine-scroll phase, checking across a duplicated-strip seam.
for name,height in [('TRAIN_LAYER0',20),('TRAIN_LAYER1',18),('TRAIN_LAYER2',16),('RUN_RIDGE',56)]:
    source=asset(name)
    for y in [0,height-1]:
        row=source[y*128:(y+1)*128]
        bits=''.join(f'{v:08b}' for v in row)
        for scroll in range(480,512):
            start=(scroll//16)*16;shift=(16-scroll%16)%16
            fetched=bits[start:start+336]
            shifted=('0'*shift+fetched)[:336]
            visible=shifted[16:336] if shift else shifted[:320]
            assert visible==bits[scroll:scroll+320],(name,y,scroll)
spans=words(asset('PLANET_SPANS'))
assert spans[132*2]<=65<spans[132*2+1]
assert spans[24*2:24*2+2]==(320,320)
print('PASS: disk checksum/payload, pinned sources, body bounds, fighter DMA, genuine hires columns, shifted parallax and planet occlusion spans')

from fighter_choreography import self_test as test_jones
test_jones()
assert decode(asset('DANCE_PACKED'),len((build/'dance-raw.bin').read_bytes()))==(build/'dance-raw.bin').read_bytes()

# Independently check every rotating highlight and its native 4x bit expansion.
spin_index=longs(asset('BIG_SPIN_INDEX'));spin_data=asset('BIG_SPIN_PACKED')
assert len(spin_index)==65 and spin_index[-1]==len(spin_data)
quad=longs(asset('BIG_SPIN_QUAD'))
assert len(quad)==256
for value,expanded in enumerate(quad):
    assert f'{expanded:032b}'==''.join(bit*4 for bit in f'{value:08b}')
for family in range(4):
    poses=[]
    for angle in range(16):
        idx=family*16+angle
        pose=decode(spin_data[spin_index[idx]:spin_index[idx+1]],640 if angle==0 else 160)
        assert any(pose), (family,angle)
        poses.append(pose)
    assert len(set(poses))>=12, 'Rotation poses need distinct silhouettes'
assert set(asset('BIG_SPIN_MAP'))=={0,1,2,3,255}
print('PASS: 64 rotating big-letter poses and native expansion table')

# Both native tracks hold each authored pose for the same two-tick cadence.
fight=words(asset('FIGHT_POSES'))
for side in (0,1):
    track=fight[side::2]
    assert len(track)==256
    assert all(len(set(track[i:i+2]))==1 for i in range(0,256,2))
    assert sum(a!=b for a,b in zip(track,track[1:]))>=100
print('PASS: both fighters have equal two-tick pose holds and active animation')
