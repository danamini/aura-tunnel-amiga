"""Compact rotating AI/ZX highlights; upright poses retain native hires detail."""
from PIL import Image
from roto_codec import encode, decode

def generate(text, strip):
    families='AIZX';packed=bytearray();offsets=[0]
    for char in families:
        x=text.index(char)*128;tile=strip.crop((x,0,x+128,40))
        for angle in range(16):
            if angle:
                logical=tile.resize((64,80),Image.Resampling.NEAREST)
                spin=logical.rotate(-angle*22.5,Image.Resampling.NEAREST,expand=True)
                spin.thumbnail((60,76),Image.Resampling.NEAREST)
                frame=Image.new('1',(64,80))
                frame.paste(spin,((64-spin.width)//2,(80-spin.height)//2))
                frame=frame.resize((32,40),Image.Resampling.NEAREST)
            else:frame=tile
            raw=frame.tobytes();data=encode(raw)
            assert decode(data,len(raw))==raw
            packed.extend(data);offsets.append(len(packed))
    mapping=bytes(families.index(c) if c in families else 255 for c in text)
    expanded=[]
    for value in range(256):
        expanded.append(sum(15<<(bit*4) for bit in range(8) if value&(1<<bit)))
    return mapping,offsets,bytes(packed),expanded
