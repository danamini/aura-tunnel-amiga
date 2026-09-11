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
sprites=asset('FIGHTER_SPRITES')
assert len(sprites)==47*3*232
assert len({sprites[i:i+696] for i in range(0,len(sprites),696)})>35
for offset in range(0,len(sprites),232):
    pos,ctl=struct.unpack_from('>HH',sprites,offset)
    assert (ctl>>8)-(pos>>8)==56
    assert sprites[offset+228:offset+232]==bytes(4)
assert any(((b>>i)&1)!=((b>>(i+1))&1) for b in asset('HI_BITMAP') for i in (0,2,4,6)), 'Hires just doubled pixels'
chrome=words(asset('HI_CHROME'))
assert len(chrome)==64*14 and all(c<4096 for c in chrome)
assert len(set(chrome))>20, 'Chrome reflection needs a varied OCS ramp'
assert max(struct.unpack('>'+'h'*(len(asset('HI_SINE'))//2),asset('HI_SINE')))+((56-GLYPH_HEIGHT)//2)*80+(GLYPH_HEIGHT-1)*80+79<4480
# Every elastic program covers all 56 destination rows exactly once, with
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
            assert source%80==0 and source+(count-1)*(80+mod)<4480
            occupied+=count
        end+=count
    assert end==56
    heights.append(occupied)
assert min(heights)<20 and max(heights)==56,'Elastic range too subtle'
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
bitmap=asset('HI_BITMAP')
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
