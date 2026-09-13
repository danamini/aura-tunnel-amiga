"""Build compact individual-letter rotations for an OCS blitter scroller."""
from PIL import Image
from hud_font import glyph
from roto_codec import encode, decode
MESSAGE = ('   SAME TEN SCENES / ZX SPECTRUM TO AMIGA / AI HELPING ME CREATE AND LEARN / '
           'Z80 TO 68000 / COPPER BLITTER SPRITES AND PAULA / MORE COLOUR SAME IDEA /   ')

def generate():
    alphabet=sorted(set(MESSAGE));raw=bytearray()
    for char in alphabet:
        tile=Image.new('1',(16,16))
        tile.paste(glyph(char).resize((12,12),Image.Resampling.NEAREST),(2,2))
        for angle in range(16):
            rotated=tile.rotate(-angle*22.5,resample=Image.Resampling.NEAREST)
            for y in range(16):
                word=sum(bool(rotated.getpixel((x,y)))<<(15-x) for x in range(16))
                raw.extend(word.to_bytes(2,'big'))
    assert len(raw)<=17280, 'Scene scratch capacity'
    compressed=encode(raw);assert decode(compressed,len(raw))==raw
    return bytes(alphabet.index(c) for c in MESSAGE),compressed,bytes(raw)
