"""Small depth-sorted orbital reactor, baked into masked OCS blitter objects."""
import math
from PIL import Image, ImageDraw
from roto_codec import encode, decode

FRAMES = 16
WIDTH = 96
HEIGHT = 96
ROW_BYTES = (WIDTH+16)//8  # trailing zero word for the blitter shifter
PLANE_BYTES = ROW_BYTES*HEIGHT
POSE_BYTES = PLANE_BYTES*2
X, Y = 112, 64


def frame(phase):
    angle = phase*math.tau/FRAMES
    cy, sy = math.cos(angle), math.sin(angle)
    tilt = .48 + .18*math.sin(angle)
    ct, st = math.cos(tilt), math.sin(tilt)
    def transform(p):
        x,y,z=p
        x,z=x*cy+z*sy,-x*sy+z*cy
        y,z=y*ct-z*st,y*st+z*ct
        return x,y,z
    def project(p):
        x,y,z=p
        scale=170/(170+z)
        return (48+x*scale,48+y*scale)
    faces=[]
    # Three solid hoops: a station silhouette, not only a wireframe diagram.
    for axis,radius in enumerate((38,34,30)):
        def vertex(t,r):
            a,b=math.cos(t)*r,math.sin(t)*r
            return transform(((a,b,0),(a,0,b),(0,a,b))[axis])
        for n in range(32):
            t=n*math.tau/32;u=(n+1)*math.tau/32
            points=[vertex(t,radius-2),vertex(t,radius+2),vertex(u,radius+2),vertex(u,radius-2)]
            depth=sum(p[2] for p in points)/4
            colour=1 if depth>6 else 2 if n%8 not in (0,1) else 3
            faces.append((depth,[project(p) for p in points],colour))
    im=Image.new('P',(WIDTH,HEIGHT));draw=ImageDraw.Draw(im)
    def rings(front):
        for depth,points,colour in sorted(faces,reverse=True):
            if (depth<=0)==front:draw.polygon(points,fill=colour)
    rings(False)
    # A lit reactor orb and four docking arms give the nested rings a centre.
    for n in range(4):
        t=angle+n*math.pi/2
        a=project(transform((math.cos(t)*12,math.sin(t)*12,0)))
        b=project(transform((math.cos(t)*29,math.sin(t)*29,0)))
        draw.line((a,b),fill=1,width=3)
        draw.line((a,b),fill=2,width=1)
    draw.ellipse((35,35,61,61),fill=1)
    draw.ellipse((37,36,59,58),fill=2)
    pulse=2+round(2*(1+math.sin(angle*2)))
    draw.ellipse((48-pulse,46-pulse,48+pulse,46+pulse),fill=3)
    draw.arc((39,38,57,56),phase*22.5,phase*22.5+210,fill=3,width=1)
    rings(True)
    # Bright orbiting beacons, depth sorted with the station hoops.
    for n in range(3):
        p=transform((math.cos(angle+n*math.tau/3)*40,math.sin(angle+n*math.tau/3)*40,0))
        x,y=project(p)
        draw.rectangle((round(x)-1,round(y)-1,round(x)+1,round(y)+1),fill=3)
    return im


def generate():
    packed=bytearray();index=[0]
    for phase in range(FRAMES):
        im=frame(phase)
        raw=bytearray()
        for plane in range(2):
            for y in range(HEIGHT):
                for x in range(0,WIDTH,8):
                    raw.append(sum(((im.getpixel((x+b,y))>>plane)&1)<<(7-b) for b in range(8)))
                raw.extend(bytes(2))
        assert len(raw)==POSE_BYTES
        data=encode(raw)
        assert decode(data,POSE_BYTES)==raw
        packed.extend(data);index.append(len(packed))
    return index,bytes(packed)
