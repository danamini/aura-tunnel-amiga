"""Flat-shaded solid shapes, padded for the OCS masked BOB blitter."""
import math
from PIL import Image, ImageDraw
from roto_codec import encode

FRAMES = 16
# A large centrepiece and four independently tumbling satellite families.
SHAPES = [('cube',64),('box',32),('octahedron',40),('tetrahedron',32),('prism',32)]

def geometry(kind):
    if kind in ('cube','box'):
        v=[(x,y,z) for z in (-1,1) for y in (-1,1) for x in (-1,1)]
        if kind=='box':v=[(x*1.3,y*.65,z*.8) for x,y,z in v]
        return v,[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)]
    if kind=='octahedron':
        return [(1,0,0),(-1,0,0),(0,1.4,0),(0,-1.4,0),(0,0,1),(0,0,-1)],[(y,x,z) for y in (2,3) for x in (0,1) for z in (4,5)]
    if kind=='tetrahedron':
        return [(1,1,1),(-1,-1,1),(-1,1,-1),(1,-1,-1)],[(0,1,2),(0,3,1),(0,2,3),(1,3,2)]
    return [(math.cos(i*math.tau/3),y,math.sin(i*math.tau/3)) for y in (-.9,.9) for i in range(3)],[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)]

def pose(kind,size,phase,ordinal):
    vertices,faces=geometry(kind)
    a=(phase/FRAMES*(1 if ordinal%2==0 else -1)+ordinal*.17)*math.tau
    b=.5+math.sin(phase*math.tau/FRAMES+ordinal)*.8
    c=.22*math.sin(phase*math.tau/FRAMES+ordinal*1.5)
    scale=.255+.035*math.sin(phase*math.tau/FRAMES+ordinal)
    transformed=[]
    for x,y,z in vertices:
        x,z=x*math.cos(a)+z*math.sin(a),-x*math.sin(a)+z*math.cos(a)
        y,z=y*math.cos(b)-z*math.sin(b),y*math.sin(b)+z*math.cos(b)
        x,y=x*math.cos(c)-y*math.sin(c),x*math.sin(c)+y*math.cos(c)
        depth=1/(1-z*.11)
        transformed.append((size/2+x*size*scale*depth,size/2+y*size*scale*depth,z))
    im=Image.new('P',(size,size));draw=ImageDraw.Draw(im)
    for i,face in sorted(enumerate(faces),key=lambda item:sum(transformed[k][2] for k in item[1])/len(item[1])):
        points=[transformed[k][:2] for k in face]
        # Face identity is stable; bright edge accents make the silhouette legible.
        draw.polygon(points,fill=1+(i+ordinal)%3)
        if i%3==0:draw.line(points+[points[0]],fill=3,width=1)
    width=((size+15)//16+1)*16
    padded=Image.new('P',(width,size));padded.paste(im)
    planes=[padded.point(lambda p:255 if p&(1<<bit) else 0,'1').tobytes() for bit in range(2)]
    mask=padded.point(lambda p:255 if p else 0,'1').tobytes()
    return b''.join(planes)+mask,im

def generate():
    packed=bytearray();index=[0];offsets=[];offset=0;previews=[]
    for i,(kind,size) in enumerate(SHAPES):
        offsets.append(offset);offset+=((size+15)//16+1)*2*size*3
        poses=[]
        for phase in range(FRAMES):
            raw,im=pose(kind,size,phase,i)
            poses.append(raw[:len(raw)*2//3])
            if phase%4==0:previews.append((phase,i,im))
        packed.extend(encode(b''.join(poses)));index.append(len(packed))
    return index,bytes(packed),offsets,offset,previews

if __name__=='__main__':
    index,packed,offsets,size,_=generate()
    print(len(packed),size,offsets)
