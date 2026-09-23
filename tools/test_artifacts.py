"""Validate the built disk and native streams, independently of rendering code."""
from pathlib import Path
import hashlib,json,struct
from hires_font import GLYPH_HEIGHT
from tunnel_geometry import PHASES, FRAME_BYTES, RING_BYTES, SECTORS

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
# Pose-specific ground lines are derived from actual opaque sprite rows.
feet=words(asset('FIGHTER_FEET'))
assert len(feet)==len(fi)-1
for pose,bottom in enumerate(feet):
    raw=sprites[pose*696:(pose+1)*696]
    occupied=[y for y in range(56) if any(any(raw[segment*232+4+y*4:segment*232+8+y*4]) for segment in range(3))]
    assert max(occupied)+1==bottom and 0<bottom<=56
print('PASS: all fighter foot anchors match actual opaque pixels')
assert any(((b>>i)&1)!=((b>>(i+1))&1) for b in decode(asset('HI_BITMAP_PACKED'),len((build/'hi-bitmap-raw.bin').read_bytes())) for i in (0,2,4,6)), 'Hires just doubled pixels'
chrome=words(asset('HI_CHROME'))
assert len(chrome)==64*36 and all(c<4096 for c in chrome)
assert len(set(chrome))>20, 'Chrome reflection needs a varied OCS ramp'
# Every elastic program covers all 72 destination rows exactly once, with
# either consecutive source rows or a repeated row. No crop reads past scratch.
stretch_size=int(__import__('re').search(r'HI_STRETCH_SIZE equ (\d+)',(build/'assets.i').read_text())[1])
stretch=decode(asset('HI_STRETCH_PACKED'),stretch_size);heights=[]
assert 320+len(stretch)<=10240
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
assert len(asset('TUNNEL_COLOURS'))==64*3*2
vertices=asset('TUNNEL')
assert len(vertices)==PHASES*FRAME_BYTES
for off in range(0,len(vertices),RING_BYTES):
    assert words(vertices[off:off+2])[0] in (1,2,3)
    points=list(zip(vertices[off+2:off+RING_BYTES:2],vertices[off+3:off+RING_BYTES:2]))
    assert len(points)==SECTORS+1
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
for start in range(len(wave)//2):
    phase=start;x=0
    while x<640:
        count,offset=wave[phase*2:phase*2+2]
        count=min(count,640-x)
        assert count>0 and count%2==0
        assert 0<=offset and offset+(GLYPH_HEIGHT-1)*80+79<5760
        phase=(phase+count//2)%(len(wave)//2);x+=count
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
from space_reactor import FRAMES as REACTOR_FRAMES, ROW_BYTES, HEIGHT as REACTOR_HEIGHT, PLANE_BYTES, POSE_BYTES, X as REACTOR_X, Y as REACTOR_Y
background=decode(asset('SPACE_BACKGROUND_PACKED'),20480)
assert any(background[:10240]) and any(background[10240:])
reactor_index=longs(asset('REACTOR_INDEX'));reactor_data=asset('REACTOR_PACKED')
assert len(reactor_index)==REACTOR_FRAMES+1 and reactor_index[-1]==len(reactor_data)
assert PLANE_BYTES*3<=5120
assert 0<=REACTOR_X and REACTOR_X+ROW_BYTES*8<=320
assert 24<=REACTOR_Y and REACTOR_Y+REACTOR_HEIGHT<=200
reactor_poses=[]
for start,end in zip(reactor_index,reactor_index[1:]):
    pose=decode(reactor_data[start:end],POSE_BYTES)
    mask=bytes(a|b for a,b in zip(pose[:PLANE_BYTES],pose[PLANE_BYTES:]))
    assert 500<sum(v.bit_count() for v in mask)<4000, 'Empty or solid reactor'
    for plane in (pose[:PLANE_BYTES],pose[PLANE_BYTES:],mask):
        assert all(plane[row*ROW_BYTES+ROW_BYTES-2:(row+1)*ROW_BYTES]==bytes(2) for row in range(REACTOR_HEIGHT))
    reactor_poses.append(pose)
assert len(set(reactor_poses))==REACTOR_FRAMES
print('PASS: reactor poses, generated silhouette, DMA bounds and compressed galaxy')
print('PASS: disk checksum/payload, pinned sources, body bounds, fighter DMA, genuine hires columns, shifted parallax and planet occlusion spans')

from fighter_choreography import self_test as test_jones
test_jones()
assert decode(asset('DANCE_PACKED'),len((build/'dance-raw.bin').read_bytes()))==(build/'dance-raw.bin').read_bytes()

# Check every rotation retains native hires detail, including diagonal edges.
from big_spins import POSE_BYTES
spin_index=longs(asset('BIG_SPIN_INDEX'));spin_data=asset('BIG_SPIN_PACKED')
assert len(spin_index)==129 and spin_index[-1]==len(spin_data)
for family in range(8):
    poses=[]
    for angle in range(16):
        idx=family*16+angle
        pose=decode(spin_data[spin_index[idx]:spin_index[idx+1]],POSE_BYTES)
        assert any(pose), (family,angle)
        if angle%4:
            fine_edges=sum(((byte>>bit)&1)!=((byte>>(bit+1))&1) for byte in pose for bit in (0,1,2,4,5,6))
            assert fine_edges>20, 'Rotation still repeats four-pixel blocks'
        poses.append(pose)
    assert len(set(poses))>=12, 'Rotation poses need distinct silhouettes'
assert set(asset('BIG_SPIN_MAP'))==set(range(8))|{255}
print('PASS: 128 full-resolution rotating big-letter poses')

# Both native tracks hold each authored pose for the same two-tick cadence.
fight=words(asset('FIGHT_POSES'))
for side in (0,1):
    track=fight[side::2]
    assert len(track)==256
    assert all(len(set(track[i:i+2]))==1 for i in range(0,256,2))
    assert sum(a!=b for a,b in zip(track,track[1:]))>=100
print('PASS: both fighters have equal two-tick pose holds and active animation')

# Every solid must fit its cache, retain its mask and leave the barrel-shift pad clear.
from solid_shapes import SHAPES, FRAMES as SOLID_FRAMES
ci=longs(asset('SOLID_INDEX'));cp=asset('SOLID_PACKED')
layout=list(struct.iter_unpack('>HHHH',asset('SOLID_LAYOUT')))
assert len(ci)==len(SHAPES)+1 and ci[-1]==len(cp) and len(layout)==len(SHAPES)
cache_size=sum(plane*3 for _,_,_,plane in layout)
assert cache_size<=5120
capacities=[20480,10240,10240,6400,7040]
for (a,b),(_,height,width,plane),capacity in zip(zip(ci,ci[1:]),layout,capacities):
    bank=decode(cp[a:b],plane*2*SOLID_FRAMES)
    assert len(bank)<=capacity
    poses=[bank[p*plane*2:(p+1)*plane*2] for p in range(SOLID_FRAMES)]
    assert len(set(poses))==SOLID_FRAMES
    for raw in poses:
        left=raw[:plane];right=raw[plane:]
        assert any(left) and any(right)
        mask=bytes(a|b for a,b in zip(left,right))
        stride=width*2
        for y in range(height):
            assert mask[(y+1)*stride-2:(y+1)*stride]==bytes(2), 'Solid padding word'
assert len(set(words(asset('SOLID_COLOURS'))))>80
# Bound all satellite blits over the full scene, including their shift padding.
sine=[v if v<32768 else v-65536 for v in words(asset('SINE'))]
for frame in range(512):
    for satellite in range(6):
        _,height,width,_=layout[1+satellite%4]
        phase=(frame//2+satellite*43)%256
        x=160+7*sine[phase]-height//2
        y=114+3*sine[(phase+64)%256]-height//2
        assert x>=0 and (x//16)*16+width*16<=320 and 24<=y and y+height<=200
brief=decode(asset('BRIEF_PACKED'),5760)
assert len(brief)==5760 and any(brief)
print('PASS: five solid families, bounded masks, colour reflections and briefing cache')
from roto_background import half_turn, decode as decode_background, encode as encode_background, ANGLE_STEPS, CYCLE_PHASES, POSE_BYTES as BG_POSE_BYTES, TOP as BG_TOP, HEIGHT as BG_HEIGHT
bg_index=longs(asset('ROTO_BG_INDEX'));bg_packed=asset('ROTO_BG_PACKED')
assert len(bg_index)==ANGLE_STEPS+1 and bg_index[-1]==len(bg_packed)
bg_poses=[decode_background(bg_packed[a:b],BG_POSE_BYTES) for a,b in zip(bg_index,bg_index[1:])]
assert len(set(bg_poses))==ANGLE_STEPS and all(any(p) for p in bg_poses)
assert BG_TOP>=24 and BG_TOP+BG_HEIGHT<=200 and BG_POSE_BYTES==40*BG_HEIGHT
cycle=bg_poses+[half_turn(p) for p in bg_poses]
assert len(set(cycle))==CYCLE_PHASES and all(half_turn(half_turn(p))==p for p in bg_poses)
# Verify both halves, including wrap, against direct counterclockwise rotation.
from PIL import Image, ImageFilter
source=Image.open(build/'roto-background.png').convert('L').filter(ImageFilter.GaussianBlur(.7))
for phase,raw in enumerate(cycle):
    direct=source.rotate(phase*360/CYCLE_PHASES,Image.Resampling.BICUBIC,center=(160,112))
    direct=direct.crop((0,BG_TOP,320,BG_TOP+BG_HEIGHT)).point(lambda p:255 if p>=115 else 0,mode='1').tobytes()
    assert raw==direct, f'Counterclockwise backdrop pose {phase}'
sunset=decode(asset('SUNSET_LOW'),20480)+decode(asset('SUNSET_HIGH'),10240)
from PIL import Image
sunset_image=Image.open(build/'sunset-asset.png')
expected_sunset=b''.join(sunset_image.point(lambda p:255 if p&(1<<plane) else 0,'1').tobytes() for plane in range(3))
assert sunset==expected_sunset,'Sunset compression changed the picture'
for raw in (bytes(7040),b'\xff\xff'*3500,bytes(range(256))*4):
    assert decode_background(encode_background(raw),len(raw))==raw
for data,size in ((b'',2),(b'\x00\x00',2),(b'\x80\x02\x00\x00',2),(b'\x00\x01',2),(b'\x00\x01ABCD',2)):
    try:decode_background(data,size)
    except ValueError:pass
    else:raise AssertionError('Malformed background stream accepted')
print('PASS: full counterclockwise backdrop rotation and exact sunset cache')
# Independent parts, full waveform cycles, and safe Paula DMA descriptors.
from music import PAL_CLOCK, WAVE_SIZE, STEP_TICKS, SECTION_STEPS, SCENE_THEMES
packed=words(asset('VOLUME_TRACK'))
assert len(packed)==2560
tracks=[[(v>>shift)&15 for v in packed] for shift in (12,8,4,0)]
assert len({tuple(t) for t in tracks})==4
assert all(max(t)>=9 and 0 in t and len(set(t))>=3 for t in tracks)
notes=list(struct.iter_unpack('>HH',asset('SCORE')))
assert len(notes)==256*4
instruments=list(struct.iter_unpack('>IHH',asset('MUSIC_INSTRUMENTS')))
samples=asset('MUSIC_SAMPLES')
assert len(instruments)==13
for i,(offset,length,_) in enumerate(instruments):
    assert offset%2==0 and length>0 and offset+length*2<=len(samples)
    if i<8:
        assert length*2==WAVE_SIZE
        signed=[v if v<128 else v-256 for v in samples[offset:offset+length*2]]
        assert abs(sum(signed))<=WAVE_SIZE and max(signed)>40 and min(signed)<-40
assert samples[instruments[-1][0]:]==bytes(2), 'One-shot silent loop'
for per,instrument in notes:
    assert per==0 or 124<=per<=65535
    assert instrument<len(instruments)-1
for section in range(4):
    start=section*SECTION_STEPS*4
    rows=notes[start:start+SECTION_STEPS*4]
    assert {i for _,i in rows[0::4]}=={section}, 'Section lead timbre'
    assert len({p for p,_ in rows[2::4] if p})>=6, 'Arpeggio must move'
    assert {i for p,i in rows[3::4] if p}=={8,9,10,11}, 'Complete drum kit'
assert bytes(SCENE_THEMES)==asset('MUSIC_SCENES')
# Check authored lead pitches against the untouched reference stream's note list.
import ast
source=ast.parse((ref/'tools/gen_ay128.py').read_text())
# The four melody literals are read as data, without re-running the generator.
melodies=[]
for node in source.body:
    if not isinstance(node,ast.Assign): continue
    names=[t.id for t in node.targets if isinstance(t,ast.Name)]
    if 'MELODY' in names and isinstance(node.value,ast.List):
        melodies.extend(ast.literal_eval(node.value)[:64])
    elif any(name in ('DRIVE','ODE','NIGHT') for name in names):
        melodies.extend(None if n=='-' else n for n in ast.literal_eval(node.value.func.value).split())
from music import pitch
assert len(melodies)==256
for step,note in enumerate(melodies):
    per=notes[step*4][0]
    if note:
        expected=440*2**((pitch(note)-69)/12)
        assert abs(1200*__import__('math').log2(PAL_CLOCK/(WAVE_SIZE*per)/expected))<7
    else: assert per==0
print('PASS: four independent parts, four themes, correct pitches and one-shot DMA banks')
# Reproduce all foreground stamp addresses over the complete train scene.
import math
for frame in range(512):
    for leaf in range(16):
        x=(leaf*37-(5+(leaf&3))*frame)&511
        if x>=304:continue
        y=((leaf*29+round(math.sin(((frame+leaf)&255)*math.tau/256)*16))&127)+48
        off=y*40+(x//16)*2
        assert x//16*2+4<=40 and 24*40<=off and off+84<=200*40
print('PASS: compact cube bank, roto backdrop, four-part music and leaf write bounds')

# The fast right-facing bank is an exact bit mirror of the source Jones poses.
ri=longs(asset('RIGHT_FIGHTER_INDEX'));rp=asset('RIGHT_FIGHTER_PACKED')
assert len(ri)==48 and ri[-1]==len(rp)
for pose,(a,b) in enumerate(zip(ri,ri[1:])):
    mirrored=decode(rp[a:b],696);original=sprites[(56+pose)*696:(57+pose)*696]
    for segment in range(3):
        for row in range(56):
            for plane in range(2):
                off=4+row*4+plane*2
                source=int.from_bytes(original[(2-segment)*232+off:(2-segment)*232+off+2],'big')
                target=int.from_bytes(mirrored[segment*232+off:segment*232+off+2],'big')
                assert f'{target:016b}'==f'{source:016b}'[::-1]
print('PASS: all 47 baked Jones poses match the original bit mirror')
