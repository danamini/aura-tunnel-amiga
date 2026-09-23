"""Check FS-UAE's actual Paula registers and stream pointers against robotsound."""
from pathlib import Path
import json
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from read_snapshot import inspect
from music import Music

result, saved = inspect(sys.argv[1] if len(sys.argv)>1 else ROOT/'emulator-data/states/Saved State 1.uss')
release = Path((ROOT/'emulator-data/loaded-build.txt').read_text().strip())
listing = (release/'demo.lst').read_text()
symbol = lambda name: int(re.search(r'^'+name+r'\s+[AE]:([0-9A-Fa-f]+)$',listing,re.M)[1],16)
memory = saved['CRAM']
u16 = lambda addr: struct.unpack_from('>H',memory,addr)[0]
u32 = lambda addr: struct.unpack_from('>I',memory,addr)[0]
assets = result['base'] + symbol('assets')
state = result['state']
# Read immutable inputs saved with the launched disk, never a later build.
disk = (release/'aura-tunnel-amiga.adf').read_bytes()
manifest = json.loads((release/'assets.json').read_text())
binary = (release/'demo.bin').read_bytes()
bank = manifest['MUSIC_SAMPLES']
bank_base = assets+bank['offset']
samples = binary[symbol('assets')+bank['offset']:symbol('assets')+bank['offset']+bank['size']]
score_offset = 1024+((len(binary)+511)&~511)
score = disk[score_offset:]
music = Music(score,samples)
loops, tick = u16(state+symbol('MUSIC_LOOPS')), u16(state+symbol('MUSIC_TICK'))
assert result['ticks'] == loops*music.ticks+tick, 'Scene input reset the music clock'
assert result['ticks'] > 0
expected = None
# Two passes suffice: loop state persists, stream offsets and register writes repeat.
count = ((music.ticks if loops else 0)+tick) or music.ticks
for expected in music.frames(count):
    pass
score_base = u32(state+symbol('MUSIC_SCORE'))
assert 0xc00000 <= score_base < 0xc80000
slow = saved['BRAM']
assert slow[score_base-0xc00000:score_base-0xc00000+4] == b'LSP1'
lsp = result['base']+symbol('LSP_State')
assert u32(lsp) == score_base+expected['byte_offset'], 'Byte stream position'
assert u32(lsp+4) == score_base+expected['word_offset'], 'Word stream position'
meter_word = struct.unpack_from('>H',score,symbol('MUSIC_LEVEL_OFFSET')+((tick-1)%music.ticks)*2)[0]
levels = [0 if result['muted'] else (meter_word>>(12-c*4))&15 for c in range(4)]
assert levels == [u16(state+symbol('LEVELS')+c*2) for c in range(4)]
voices = []
for c in range(4):
    volume = 0 if result['muted'] else expected['volumes'][c]
    audio = saved[f'AUD{c}']
    length, remaining, period = struct.unpack_from('>HHH',audio,4)
    loop, pointer = struct.unpack_from('>II',audio,12)
    assert audio[1] == volume == u16(state+symbol('VOLUMES')+c*2), (c,audio[1],volume)
    assert period == expected['periods'][c], (c,period,expected['periods'][c])
    assert loop == bank_base+expected['pointers'][c], (c,loop,expected['pointers'][c])
    assert length == expected['lengths'][c], (c,length,expected['lengths'][c])
    assert bank_base <= pointer <= bank_base+len(samples), (c,pointer)
    voices.append({'channel':c,'volume':volume,'period':period,'loop_words':length,
                   'remaining_words':remaining,'dma_pointer':pointer,'loop_pointer':loop})
result.update(levels=levels,music_tick=tick,music_loops=loops,score_address=score_base,
              paused=bool(u16(state+symbol('PAUSED'))),voices=voices)
path = ROOT/'validation/robotsound-native.json'
history = json.loads(path.read_text()) if path.exists() else []
if not history or history[-1] != result:
    history.append(result)
path.write_text(json.dumps(history,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='performance'},indent=2))
