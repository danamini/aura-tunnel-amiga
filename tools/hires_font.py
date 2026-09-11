"""Resample the original vector strokes at half-pixel horizontal intervals."""
import math, struct
from PIL import Image
GLYPH_HEIGHT=40

def generate(font,text,output):
    columns=[]
    for char in text:
        for x in range(64):
            pattern=0;px=(x+.5)/2-.5
            for y in range(GLYPH_HEIGHT):
                py=(y+.5)*24/GLYPH_HEIGHT-.5
                lit=False
                for path in font.STROKES[char]:
                    for (x0,y0),(x1,y1) in zip(path,path[1:]):
                        dx=x1-x0;dy=y1-y0
                        t=max(0,min(1,((px-x0)*dx+(py-y0)*dy)/(dx*dx+dy*dy)))
                        if math.hypot(px-x0-t*dx,py-y0-t*dy)<=2.45:lit=True
                pattern|=int(lit)<<y
            columns.append(pattern)
    im=Image.new('1',(len(columns),GLYPH_HEIGHT))
    for x,p in enumerate(columns):
        for y in range(GLYPH_HEIGHT):im.putpixel((x,y),(p>>y)&1)
    im.save(output/'hires-lettering.png')
    width=len(columns)+656
    bitmap=bytes(sum(((columns[(x+b)%len(columns)]>>y)&1)<<(7-b) for b in range(8))
                 for y in range(GLYPH_HEIGHT) for x in range(0,width,8))
    return len(columns),bitmap,width//8
