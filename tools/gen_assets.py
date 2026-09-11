"""Bake DMA assets, preserving a pinned Spectrum score, lettering and poses.

No screen recording: the 68000 renders scenes, Copper colours the raster,
blitter moves planar objects and Paula plays the score on four DMA channels.
"""
from pathlib import Path
import importlib.util, json, math, random, re, struct, sys
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT/'assets/reference'
OUT = ROOT/'build'
OUT.mkdir(exist_ok=True)
blob = bytearray()
symbols = []
manifest = {}

def put(name, data):
    if len(blob) & 1: blob.append(0)
    symbols.append(f'{name} equ {len(blob)}')
    manifest[name] = {'offset':len(blob), 'size':len(data)}
    blob.extend(data)

def words(values): return struct.pack('>'+'H'*len(values), *(v & 65535 for v in values))
def longs(values): return struct.pack('>'+'I'*len(values), *values)

def bits(im):
    w,h=im.size
    assert w%8==0
    return bytes(sum((1 if im.getpixel((x+b,y)) else 0)<<(7-b) for b in range(8))
                 for y in range(h) for x in range(0,w,8))

# A bundled Pillow raster font is converted to fixed 8x8 cells at build time.
# The original 32x24 outlined Spectrum display font is preserved below.
font=ImageFont.load_default(size=8)
glyphs=[]
for c in range(32,128):
    im=Image.new('1',(8,8));ImageDraw.Draw(im).text((0,-2),chr(c),font=font,fill=1)
    glyphs.append(im)
put('SMALLFONT',b''.join(bits(g) for g in glyphs))

def text_image(lines, height=8):
    im=Image.new('1',(320,height))
    for x,y,text in lines:
        for n,c in enumerate(text):
            if 32<=ord(c)<128: im.paste(glyphs[ord(c)-32],(x+n*8,y))
    return im

names=['BRIEFING','NEON TUNNEL','COPPER ROTO','STAR SNAKE','SINE SCROLL',
       'SOLID CUBES','DOT RUNNER','DEEP SPACE','3D GRAPHS','NIGHT TRAIN']
durations=[256,512,512,256,1536,512,768,256,512,512]
put('DURATIONS',words(durations))
put('HEADERS',b''.join(bits(text_image([(8,0,f'{i+1:02} / {name}'),(232,0,'A500 OCS')])) for i,name in enumerate(names)))
put('FPS_LABEL',bits(text_image([(8,0,'AMIGA 500 / PAL'),(264,0,'FPS')])) )
put('FOOTER',bits(text_image([(8,0,'AURA TUNNEL / FOUR VOICES / SAME SHOW')])) )
put('RUN_HELP',bits(text_image([(8,0,'PRESS R: BODIES / DOTS')])) )
brief=['AURA TUNNEL','AMIGA 500 / OCS','TEN SCENES','EVERYTHING BAKED.','SHARING THE BEAM','READY']
put('BRIEF',bits(text_image([(32,i*24,s) for i,s in enumerate(brief)],144)))
put('RUN_SPEEDS',bits(text_image([(32,0,'SLOW'),(240,0,'FAST')])) )
put('GRAPH_COMPARE',bits(text_image([(8,0,'ZX ROM BASIC: 159.15S / 1363 POINTS'),(8,12,'A500 NATIVE:      MS   ~     X FASTER'),(8,24,'FIXED POINT VS BASIC / NOT CPU RATIO')],36)))
put('GRAPH_LIVE_TITLE',bits(text_image([(8,0,'LIVE 68000 / FIXED-POINT EXP')])) )
put('GRAPH_BAKED_TITLE',bits(text_image([(8,0,'PRECALCULATED / BLITTER PLOT')])) )
put('GRAPH_LISTING',bits(text_image([(8,0,'Z=78*EXP(-(C*C+D*D)/1400)'),
 (8,12,'X1=X+COS(PI/4)*Y'),(8,24,'Y1=Z+COS(PI/4)*Y')],36)))

put('SINE_ROWS',words([round(math.sin(i*math.tau/256)*16)*40 for i in range(256)]))
put('SINE',words([round(math.sin(i*math.tau/256)*16) for i in range(256)]))

# Exactly the source demo's original outlined lettering, including its A/0/5.
spec=importlib.util.spec_from_file_location('spectrum_font',REF/'tools/gen_font.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
bigtext='AURA TUNNEL A500 ONE BEAM '
column_stream=[]
for c in bigtext:
    raw=mod.glyph(c)
    for x in range(32):
        column_stream.append(sum(((raw[y*4+x//8]>>(7-x%8))&1)<<y for y in range(24)))
big_columns=column_stream
symbols.append(f'BIGWIDTH equ {len(column_stream)}')
from hires_font import generate as generate_hires,GLYPH_HEIGHT
hi_columns,hi_width,hi_bitmap,hi_stride=generate_hires(mod,bigtext,OUT)
put('HI_BITMAP',hi_bitmap)
symbols.extend([f'HI_STRIDE equ {hi_stride}',f'HI_GLYPH_HEIGHT equ {GLYPH_HEIGHT}'])
put('HICOLS',words(hi_columns))
hi_base=(56-GLYPH_HEIGHT)//2
put('HI_SINE',words([round(hi_base*math.sin(i*math.tau/512))*80 for i in range(512)]))
symbols.append(f'HI_BASE_ROW equ {hi_base}')
wave=[round(hi_base*math.sin(i*math.tau/512)) for i in range(512)]
wave_runs=[]
for phase in range(512):
    n=1
    while wave[(phase+n)%512]==wave[phase]:n+=1
    wave_runs.extend((n,(wave[phase]+hi_base)*80))
put('HI_WAVE_RUNS',words(wave_runs))
symbols.append(f'HIWIDTH equ {hi_width}')
stretch=bytearray();stretch_index=[];stretch_cache={}
for phase in range(64):
    scale=.62+.38*math.cos(phase*math.tau/64)
    mapping=[]
    for y in range(56):
        source=round(27.5+(y-27.5)/scale)
        mapping.append(source if 0<=source<56 else 255)
    key=tuple(mapping)
    if key not in stretch_cache:
        stretch_cache[key]=len(stretch);y=0
        while y<56:
            source=mapping[y];step=0;count=1
            if y+1<56 and source!=255 and mapping[y+1]==source+1:step=1
            while y+count<56 and mapping[y+count]==source+step*count:count+=1
            stretch+=words([0xfffe if source==255 else source*80,y*80,count,step*80-80])
            y+=count
        stretch+=words([0xffff])
    stretch_index.append(stretch_cache[key])
put('HI_STRETCH_INDEX',words(stretch_index));put('HI_STRETCH',stretch);put('ZERO_ROW',bytes(80))
snake='        AURA TUNNEL        TUBE... BOX... STAR... TRUE HI-RES... GIANT LETTERS...   NO DOUBLE BUFFER - WE RACE THE BEAM...   THE STACK POINTER IS THE RENDERER...   SNAKE SNAKE SNAKE...   SPECTRUM AURA GOES 8-BIT...      '
put('SNAKETEXT',snake.encode()+b'\0')
symbols.append(f'SNAKECHARS equ {len(snake)}')
snake_columns=[]
for c in snake:
    g=glyphs[ord(c)-32]
    for x in range(8):snake_columns.append(sum(bool(g.getpixel((x,y)))<<y for y in range(8)))
# Specialised 68000 column painters. Each performs only its lit-pixel ORs:
# no per-pixel tests, shifts or branches at runtime. 8B29 = OR.B D5,d16(A1).
code=bytearray();offsets={}
for pattern in sorted(set(big_columns+snake_columns)):
    offsets[pattern]=len(code)
    for y in range(24):
        if pattern&(1<<y):code+=words([0x8b29,y*40])
    code+=words([0x4e75])
assert len(code)<32768
(OUT/'column-code.bin').write_bytes(code)
put('BIGCOLS',words([offsets[c] for c in big_columns*2]))
put('SNAKECOLS',words([offsets[c] for c in snake_columns*2]))
symbols.append(f'SNAKEWIDTH equ {len(snake_columns)}')

# Native line-mode tunnel: six twisted octagonal rings plus depth rails.
# Store vertices, not full frames or per-pixel masks; the blitter draws them.
tunnel=bytearray();idx=[]
for f in range(128):
    idx.append(len(tunnel));rings=[]
    depths=sorted(((ring*128/6+f)%128)/128 for ring in range(6))
    for depth in depths:
        radius=9+143*depth*depth
        cx=160+14*math.sin(f*math.tau/128+depth*2)
        cy=112+6*math.cos(f*math.tau/128+depth*3)
        angle=f*math.tau/128*.25+depth*.45
        vertices=[(max(2,min(317,round(cx+radius*math.cos(i*math.tau/8+angle)))),
                   max(26,min(196,round(cy+radius*.54*math.sin(i*math.tau/8+angle))))) for i in range(8)]
        style=2 if depth<.35 else 3 if depth>.8 else 1
        tunnel+=words([style]+[v for xy in vertices+[vertices[0]] for v in xy])
        rings.append((style,vertices))
    if f==20:
        preview=Image.new('RGB',(320,256),(3,5,20));pd=ImageDraw.Draw(preview)
        for left,right in zip(rings,rings[1:]):
            for i in range(0,8,2):pd.line([left[1][i],right[1][i]],fill=(88,64,167))
        for style,vertices in rings:pd.line(vertices+[vertices[0]],fill={1:(64,221,255),2:(113,72,194),3:(255,207,235)}[style])
        preview.resize((960,768),Image.Resampling.NEAREST).save(OUT/'neon-tunnel.png')
put('TUNNEL_INDEX',longs(idx));put('TUNNEL',tunnel)

# Roto: short native source rows. The blitter repeats each row eight times.
# 40 source bytes become a 320px tile row without 8x CPU writes.
roto=bytearray()
for f in range(64):
    a=f*math.tau/64;pitch=38+12*math.sin(f*math.tau/64)
    for row in range(20):
        colours=[]
        for col in range(320):
            x=col-160;y=(row-10)*8
            u=math.floor((x*math.cos(a)+y*math.sin(a))/pitch)
            v=math.floor((-x*math.sin(a)+y*math.cos(a))/pitch)
            colours.append(1 if (u+v)%2 else 2)
        roto.extend(sum((colours[x+b]&1)<<(7-b) for b in range(8)) for x in range(0,320,8))
put('ROTO',roto)
rd=bytearray();ri=[]
for f in range(64):
    ri.append(len(rd));a=f*math.tau/64;pitch=38+12*math.sin(f*math.tau/64)
    pts={}
    for u in range(-8,9):
        for v in range(-8,9):
            x=round(160+pitch*(u*math.cos(a)-v*math.sin(a)))
            y=round(112+pitch*(u*math.sin(a)+v*math.cos(a)))
            if 0<=x<320 and 32<=y<192:
                off=y*40+x//8;pts[off]=pts.get(off,0)|(128>>(x%8))
    rd+=words([len(pts)])
    for off,mask in pts.items():rd+=words([off])+bytes([mask,0])
put('ROTO_DOTS_INDEX',longs(ri));put('ROTO_DOTS',rd)

# Runner: three static background planes, one independently drawn overlay plane.
# Clouds, solar disc and layered silhouettes stay in CHIP RAM; no HAM carry
# state is disturbed by bright moving joints.
sunset=Image.new('P',(320,256));sd=ImageDraw.Draw(sunset)
sd.ellipse((192,90,270,168),fill=6)
sd.ellipse((196,93,266,164),fill=7)
sky_rng=random.Random(500)
for cy,cx,length in [(58,35,84),(77,122,68),(103,220,90),(120,54,98),(130,176,58)]:
    for y in range(cy,cy+7):
        inset=abs(y-cy-3)*6
        sd.line((cx-length//2+inset,y,cx+length//2-inset,y),fill=5 if y>cy+3 else 4)
        for x in range(max(0,cx-length//2),min(320,cx+length//2)):
            if sky_rng.random()<.12:sd.point((x,y+7),fill=4)
for colour,base,amp,phase in [(1,148,19,.4),(2,169,11,2.1),(3,185,5,4.2)]:
    contour=[(x,round(base+amp*(.55*math.sin(x*.033+phase)+.3*math.sin(x*.081+phase*2)+.15*math.sin(x*.19)))) for x in range(320)]
    sd.polygon(contour+[(319,199),(0,199)],fill=colour)
for x in range(320):
    if x%3!=0:sd.point((x,189+(x%5==0)),fill=2)
put('SUNSET',b''.join(bits(sunset.point(lambda p:255 if p&(1<<plane) else 0,'1')) for plane in range(3)))
stops=[(0,(1,1,3)),(24,(2,2,5)),(72,(5,3,6)),(112,(12,5,6)),(148,(15,10,6)),(196,(15,12,8)),(200,(0,0,0)),(208,(0,0,0))]
sunset_ramp=[]
for row in range(52):
    y=row*4
    a,b=next((a,b) for a,b in zip(stops,stops[1:]) if a[0]<=y<=b[0])
    t=(y-a[0])/(b[0]-a[0]);rgb=[round(c+(d-c)*t) for c,d in zip(a[1],b[1])]
    sunset_ramp.append((rgb[0]<<8)|(rgb[1]<<4)|rgb[2])
put('SUNSET_RAMP',words(sunset_ramp))
ridge=Image.new('1',(512,56));rdraw=ImageDraw.Draw(ridge)
contour=[(x,round(20+10*math.sin(x*.021)+5*math.sin(x*.064))) for x in range(512)]
rdraw.polygon(contour+[(511,55),(0,55)],fill=1)
ridge_double=Image.new('1',(1024,56));ridge_double.paste(ridge,(0,0));ridge_double.paste(ridge,(512,0))
put('RUN_RIDGE',bits(ridge_double))
preview_palette=[(20,24,48),(74,45,78),(49,31,58),(19,20,38),(204,128,136),(120,65,102),(255,210,153),(255,243,205)]
sunset.putpalette([v for c in preview_palette for v in c]+[0]*(768-24))
sunset.save(OUT/'sunset-asset.png')

# Galaxy behind live stars; the opaque planet occludes them via row spans.
space_bg=Image.new('P',(320,256))
planet_mask=Image.new('1',(320,256))
sr=random.Random(1979)
for y in range(24,200):
    for x in range(320):
        dx=(x-229)/1.45;dy=(y-84)*1.5
        r=math.hypot(dx,dy);a=math.atan2(dy,dx)
        arms=(.5+.5*math.cos(a*3-r*.15))**8
        glow=math.exp(-r*r/1900)*(.25+.75*arms)+math.exp(-r*r/85)
        noise=sr.random()*.23
        value=3 if glow>.85 else 2 if glow+noise>.42 else 1 if glow+noise>.23 else 0
        dx=x-65;dy=y-132
        rr=dx*dx+dy*dy
        if rr<27*27:
            planet_mask.putpixel((x,y),1)
            light=max(0,(-dx*.55-dy*.45+math.sqrt(27*27-rr)*.7)/27)
            value=1 if light<.25 else 2 if light<.75 else 3
            if (y+int(4*math.sin(x*.14)))%9<2 and value>1:value-=1
        space_bg.putpixel((x,y),value)
put('SPACE_BACKGROUND',b''.join(bits(space_bg.point(lambda p:255 if p&(1<<plane) else 0,'1')) for plane in range(2)))
planet_spans=[]
for y in range(256):
    covered=[x for x in range(320) if planet_mask.getpixel((x,y))]
    planet_spans.extend((min(covered),max(covered)+1) if covered else (320,320))
put('PLANET_SPANS',words(planet_spans))
# Same night-train setting, with independent skyline, lamps and rail scenery.
# Duplicate each 512px strip so a shifted 336px fetch never wraps in memory.
train_bands=[]
for layer,height in enumerate((20,18,16)):
    im=Image.new('P',(512,height));d=ImageDraw.Draw(im)
    if layer==0:
        for x in range(0,512,24):
            roof=4+(x*7)%11
            d.rectangle((x,roof,x+17,height-1),fill=1)
            for wx in range(x+3,x+16,5):
                for wy in range(roof+3,height-2,5):d.point((wx,wy),fill=2)
    elif layer==1:
        for x in range(20,512,96):
            d.line((x,0,x,height-1),fill=1,width=2)
            d.line((x-8,1,x+9,1),fill=1)
            d.rectangle((x-9,2,x-5,4),fill=3)
            d.rectangle((x+6,2,x+10,4),fill=3)
    else:
        d.line((0,3,511,3),fill=1)
        d.line((0,12,511,12),fill=2)
        for x in range(0,512,16):d.polygon([(x,5),(x+5,5),(x+12,10),(x+7,10)],fill=3)
    doubled=Image.new('P',(1024,height));doubled.paste(im,(0,0));doubled.paste(im,(512,0))
    train_bands.append(b''.join(bits(doubled.point(lambda p:255 if p&(1<<plane) else 0,'1')) for plane in range(2)))
for i,data in enumerate(train_bands):put(f'TRAIN_LAYER{i}',data)
space_bg.putpalette([5,8,24,45,23,83,149,61,155,255,195,159]+[0]*756)
space_bg.save(OUT/'space-asset.png')

# True planar flat-shaded cube poses; three face colours replace Bayer stipple.
def cube(size, phase):
    a=phase*math.tau/32;b=a*.7
    verts=[]
    for x,y,z in [(-1,-1,-1),(1,-1,-1),(-1,1,-1),(1,1,-1),(-1,-1,1),(1,-1,1),(-1,1,1),(1,1,1)]:
        x,z=x*math.cos(a)+z*math.sin(a),-x*math.sin(a)+z*math.cos(a)
        y,z=y*math.cos(b)-z*math.sin(b),y*math.sin(b)+z*math.cos(b)
        verts.append((size/2+x*size*.25,size/2+y*size*.25,z))
    im=Image.new('P',(size,size));d=ImageDraw.Draw(im)
    faces=[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)]
    for i,face in sorted(enumerate(faces),key=lambda item:sum(verts[k][2] for k in item[1])):
        d.polygon([(verts[k][0],verts[k][1]) for k in face],fill=(i%3)+1)
    padded=Image.new('P',(size+16,size));padded.paste(im,(0,0))
    return b''.join(bits(padded.point(lambda p:255 if p&(1<<plane) else 0,'1')) for plane in range(2))+bits(padded.point(lambda p:255 if p else 0,'1'))
put('CUBES',b''.join(cube(48,i) for i in range(32)))
put('MINICUBES',b''.join(cube(16,i) for i in range(32)))

# Keep the actual source runners (CMU joints), including their pose counts.
index=(REF/'build/runner-index.asm').read_text()
records=re.findall(r'dw (RUNDAT|RUNSMALL)\+(\d+)\s+db (\d+)',index)
cache=bytearray();cache_index=[]
for kind,origin in [('RUNDAT',(108,40)),('RUNSMALL',(36,116)),('RUNSMALL',(240,112))]:
    raw_pose=(REF/('build/runner.bin' if kind=='RUNDAT' else 'build/runner-small.bin')).read_bytes()
    for k,off,count in records:
        if k!=kind:continue
        cache_index.append(len(cache));masks={}
        pts=raw_pose[int(off):int(off)+int(count)*2]
        for x,y in zip(pts[0::2],pts[1::2]):
            for dx,dy in [(0,0),(1,0),(0,1),(1,1)]:
                xx=x+origin[0]+dx;yy=y+origin[1]+dy
                addr=yy*40+xx//8;masks[addr]=masks.get(addr,0)|(128>>(xx%8))
        cache+=words([len(masks)])
        for off,mask in sorted(masks.items()):cache+=words([off])+bytes([mask,0])
put('RUN_CACHE_INDEX',words(cache_index));put('RUN_CACHE',cache)
from runner_bodies import generate as generate_bodies
body_index,body_data=generate_bodies(REF,OUT)
put('BODY_INDEX',longs(body_index));put('BODY_DATA',body_data)
# 47 authored poses (guard, punches, kicks and recoveries), Puffolotti CC0.
# Keep a single canonical direction; the 68000 mirrors into an inactive DMA
# bank using a byte reversal LUT, saving another 32 KiB of CHIP memory.
source=Image.open(ROOT/'assets/fighters/mustermann.gif')
sequence=list(range(4,27))+list(range(140,164))
colours=[(28,35,51),(239,184,138),(216,139,39)]
sprite_poses=bytearray();previews=[]
for pose in sequence:
    source.seek(pose)
    rgba=source.convert('RGBA').crop((49,51,199,223)).resize((48,56),Image.Resampling.LANCZOS)
    frame=Image.new('P',(48,56))
    for y in range(56):
        for x in range(48):
            r,g,b,a=rgba.getpixel((x,y))
            if a<128:continue
            idx=min(range(3),key=lambda k:sum((v-colours[k][j])**2 for j,v in enumerate((r,g,b))))+1
            frame.putpixel((x,y),idx)
    frame.putpalette([0,0,0]+[v for c in colours for v in c]+[0]*756)
    previews.append(frame.convert('RGB'))
    for segment in range(3):
        hx=129+112+segment*16
        sprite_poses+=words([(148<<8)|(hx>>1),(204<<8)|(hx&1)])
        for y in range(56):
            for plane in range(2):
                sprite_poses+=words([sum(((frame.getpixel((segment*16+x,y))>>plane)&1)<<(15-x) for x in range(16))])
        sprite_poses+=bytes(4)
put('FIGHTER_SPRITES',sprite_poses)
fight_script=(REF/'src/main.asm').read_text().split('FIGHTS:',1)[1]
fight_steps=[]
for line in fight_script.splitlines():
    match=re.match(r'\s*db\s+(\d+),(\d+),\s*(\d+),(\d+)',line)
    if match:fight_steps.append(tuple(map(int,match.groups())))
    if len(fight_steps)==32:break
assert len(fight_steps)==32
fight_x=[]
for frame in range(256):
    i=frame//8;t=(frame%8)/8
    for side in (0,2):fight_x.append(round(10*(fight_steps[i][side]*(1-t)+fight_steps[(i+1)%32][side]*t))+129)
put('FIGHT_X',words(fight_x))
put('REVERSE_BYTE',bytes(int(f'{v:08b}'[::-1],2) for v in range(256)))
symbols.extend([f'FIGHTER_FRAMES equ {len(sequence)}','FIGHTER_SEGMENT equ 232','FIGHTER_POSE equ 696','FIGHTER_HEIGHT equ 56'])
preview=Image.new('RGB',(48*12,56*4),(12,18,32))
for i,frame in enumerate(previews):preview.paste(frame,(i%12*48,i//12*56))
preview.resize((1152,448),Image.Resampling.NEAREST).save(OUT/'fighter-poses.png')
rng=random.Random(1987)
put('STARS',b''.join(words([rng.randrange(320),24+rng.randrange(166),1+i//16]) for i in range(48)))

# Precalculated surfaces after the live formula interlude.
graphs=[]
for kind in range(3):
    im=Image.new('1',(320,128));d=ImageDraw.Draw(im);hidden=[999]*320
    for y in range(0,141,4):
        for x in range(0,141,2):
            c=x-70;v=y-70
            z=(78*math.exp(-(c*c+v*v)/1400) if kind==0 else
               25+18*math.cos(c/12)*math.cos(v/12) if kind==1 else 30+(c*c-v*v)/180)
            sx=40+int(x+.707*y);sy=124-int(z*.8+y*.5)
            if 0<=sx<320 and 0<=sy<128 and sy<hidden[sx]:
                d.point((sx,sy),fill=1);hidden[sx]=sy
    graphs.append(bits(im))
put('GRAPHS',b''.join(graphs))

# Same four-section score, arranged for Paula's four independent sample loops.
# Import in an isolated output folder: reference generator writes only there.
scoreout=OUT/'score-reference';scoreout.mkdir(exist_ok=True)
oldargv=sys.argv;sys.argv=['gen_ay128.py',str(scoreout)]
spec=importlib.util.spec_from_file_location('spectrum_score',REF/'tools/gen_ay128.py')
score=importlib.util.module_from_spec(spec);spec.loader.exec_module(score);sys.argv=oldargv
notes=bytearray()
for step,note in enumerate(score.MELODY):
    root=score.BASS[step//8]
    bass=root
    if 64<=step<128 and step%4==2:bass=root[:-1]+str(int(root[-1])+1)
    def period(n):return max(124,min(65535,round(3546895/(64*score.note_hz(n))))) if n else 0
    notes+=words([period(note),period(bass),period(root)//2,
                  420 if step%16 in (4,12) else 150])
put('SCORE',notes)
symbols.append(f'SCORE_STEPS equ {len(score.MELODY)}')
put('LEAD_SAMPLE',bytes(round(100*(1-4*abs(i/64-.5)))&255 for i in range(64)))
put('BASS_SAMPLE',bytes(round(110*math.sin(i*math.tau/64))&255 for i in range(64)))
put('PAD_SAMPLE',bytes(round(65*math.sin(i*math.tau/64)+20*math.sin(i*math.tau/32))&255 for i in range(64)))
put('DRUM_SAMPLE',bytes(rng.randrange(-95,96)&255 for _ in range(256)))
put('VOLUME_ENV',words([42,42,38,36,32,28,24,20,12,0,
 48,44,40,36,32,28,24,20,16,12, 20,20,19,19,18,18,17,17,16,16,
 38,22,10,4,0,0,0,0,0,0]))

# 16 ordered dissolve thresholds, an eight-row mask repeated vertically.
bayer=[[0,8,2,10],[12,4,14,6],[3,11,1,9],[15,7,13,5]]
put('DISSOLVE',b''.join(bytes(sum((1 if bayer[y%4][x%4]<level else 0)<<(7-x) for x in range(8)) for _ in range(40))
                       for level in range(17) for y in range(4)))

(OUT/'assets.bin').write_bytes(blob)
(OUT/'assets.i').write_text('\n'.join(symbols)+'\n')
(OUT/'assets.json').write_text(json.dumps(manifest,indent=2)+'\n')
(OUT/'scenes.json').write_text(json.dumps([{'name':n,'ticks':t} for n,t in zip(names,durations)],indent=2)+'\n')
print(f'{len(blob):,} bytes of assets; {sum(durations)/50:.2f}s scene cycle')
