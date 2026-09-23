"""Counterclockwise galaxy rotation behind the clockwise checker plane."""
from PIL import Image, ImageFilter
import struct

WIDTH = 320
TOP = 24
HEIGHT = 176
POSE_BYTES = WIDTH*HEIGHT//8
ANGLE_STEPS = 16
CYCLE_PHASES = 2*ANGLE_STEPS
TICK_SHIFT = 3


def encode(raw):
    """Word runs: positive count + literals, or bit15 count + one repeated word."""
    if len(raw)%2:raise ValueError('Word stream must be even')
    values=struct.unpack('>'+str(len(raw)//2)+'H',raw)
    out=bytearray();pos=0
    while pos<len(values):
        count=1
        while pos+count<len(values) and values[pos+count]==values[pos] and count<32767:count+=1
        if count>=2:
            out.extend(struct.pack('>HH',count|0x8000,values[pos]));pos+=count
        else:
            start=pos;pos+=1
            while pos<len(values) and (pos+1==len(values) or values[pos]!=values[pos+1]) and pos-start<32767:pos+=1
            out.extend(struct.pack('>H',pos-start))
            out.extend(struct.pack('>'+'H'*(pos-start),*values[start:pos]))
    return bytes(out)


def decode(data,size):
    if size<0 or size%2:raise ValueError('Invalid output size')
    out=bytearray();pos=0
    while len(out)<size:
        if pos+2>len(data):raise ValueError('Missing command')
        command=int.from_bytes(data[pos:pos+2],'big');pos+=2
        count=command&0x7fff
        if not count or len(out)+count*2>size:raise ValueError('Run outside output')
        length=2 if command&0x8000 else count*2
        if pos+length>len(data):raise ValueError('Missing data')
        out.extend(data[pos:pos+length]*(count if command&0x8000 else 1));pos+=length
    if pos!=len(data):raise ValueError('Trailing input')
    return bytes(out)


def half_turn(raw):
    """Rotate a packed one-bit rectangle 180 degrees without an extra pose bank."""
    reverse=bytes(int(f'{v:08b}'[::-1],2) for v in range(256))
    return raw[::-1].translate(reverse)


def generate(image):
    # Smooth isolated speckles before rotation to avoid twinkling aliases.
    source=image.convert('L').filter(ImageFilter.GaussianBlur(.7))
    index=[0];packed=bytearray()
    for phase in range(ANGLE_STEPS):
        angle=phase*180/ANGLE_STEPS
        pose=source.rotate(angle,Image.Resampling.BICUBIC,center=(160,112))
        pose=pose.crop((0,TOP,WIDTH,TOP+HEIGHT)).point(lambda p:255 if p>=115 else 0,mode='1')
        raw=pose.tobytes();data=encode(raw)
        assert len(raw)==POSE_BYTES and decode(data,POSE_BYTES)==raw
        packed.extend(data);index.append(len(packed))
    return index,bytes(packed)
