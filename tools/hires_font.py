"""Resample the original vector strokes at half-pixel horizontal intervals."""
import math, struct
from PIL import Image

def generate(font,text,output):
    columns=[]
    for char in text:
        for x in range(64):
            pattern=0;px=(x+.5)/2-.5
            for y in range(24):
                lit=False
                for path in font.STROKES[char]:
                    for (x0,y0),(x1,y1) in zip(path,path[1:]):
                        dx=x1-x0;dy=y1-y0
                        t=max(0,min(1,((px-x0)*dx+(y-y0)*dy)/(dx*dx+dy*dy)))
                        if math.hypot(px-x0-t*dx,y-y0-t*dy)<=1.15:lit=True
                pattern|=int(lit)<<y
            columns.append(pattern)
    code=bytearray();offsets={}
    for pattern in sorted(set(columns)):
        offsets[pattern]=len(code)
        for y in range(24):
            if pattern&(1<<y):code+=struct.pack('>HH',0x8b29,y*80)
        code+=b'\x4e\x75'
    assert len(code)<32768
    (output/'hires-code.bin').write_bytes(code)
    im=Image.new('1',(len(columns),24))
    for x,p in enumerate(columns):
        for y in range(24):im.putpixel((x,y),(p>>y)&1)
    im.save(output/'hires-lettering.png')
    return [offsets[p] for p in columns*2],len(columns)
