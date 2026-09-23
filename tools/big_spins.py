"""Full hires rotating letters, sampled in the display's physical aspect ratio."""
from PIL import Image
from roto_codec import encode, decode
from hires_font import GLYPH_HEIGHT

GLYPH_WIDTH = 128
POSE_BYTES = GLYPH_WIDTH * GLYPH_HEIGHT // 8

def generate(text, strip):
    families='AIZXSCTM';packed=bytearray();offsets=[0]
    for char in families:
        x=text.index(char)*GLYPH_WIDTH
        tile=strip.crop((x,0,x+GLYPH_WIDTH,GLYPH_HEIGHT))
        for angle in range(16):
            if angle:
                # Hires pixels are half as wide; Copper repeats each source row.
                # Rotate in square-pixel space at 4x scale, then area sample to
                # every actual display column. Threshold without dithering so
                # the moving one-bit silhouette stays clean.
                logical=tile.convert('L').resize((256,320),Image.Resampling.BICUBIC)
                spin=logical.rotate(-angle*22.5,Image.Resampling.BICUBIC,expand=True)
                spin.thumbnail((240,304),Image.Resampling.LANCZOS)
                frame=Image.new('L',(256,320))
                frame.paste(spin,((256-spin.width)//2,(320-spin.height)//2))
                frame=frame.resize((GLYPH_WIDTH,GLYPH_HEIGHT),Image.Resampling.LANCZOS)
                frame=frame.point(lambda value:255 if value>=128 else 0,mode='1')
            else:frame=tile
            raw=frame.tobytes();data=encode(raw)
            assert decode(data,len(raw))==raw
            packed.extend(data);offsets.append(len(packed))
    mapping=bytes(families.index(c) if c in families else 255 for c in text)
    return mapping,offsets,bytes(packed)
