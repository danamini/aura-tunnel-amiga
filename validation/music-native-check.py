"""Compare real FS-UAE Paula registers with the immutable launched music score.

AUD chunk layout: FS-UAE v3.2.35 src/audio.cpp, save_audio().
Save with F5, then run this script; each invocation appends one checked sample.
"""
from pathlib import Path
import json
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from read_snapshot import inspect
from music import STEP_TICKS, SECTION_STEPS, THEMES

result, saved = inspect(sys.argv[1] if len(sys.argv)>1 else ROOT/'emulator-data/states/Saved State 1.uss')
release = Path((ROOT/'emulator-data/loaded-build.txt').read_text().strip())
listing = (release/'demo.lst').read_text()
symbol = lambda name: int(re.search(r'^'+name+r'\s+[AE]:([0-9A-Fa-f]+)$',listing,re.M)[1],16)
memory = saved['CRAM']
u16 = lambda addr: struct.unpack_from('>H',memory,addr)[0]
assets = result['base'] + symbol('assets')
state = result['state']
music_tick = (u16(state+symbol('MUSIC_TICK'))-1) % symbol('MUSIC_TOTAL_TICKS')
assert 0 <= music_tick < symbol('MUSIC_TOTAL_TICKS')
assert u16(state+symbol('MUSIC_SCENE')) == result['scene']
theme_start = memory[assets+symbol('MUSIC_SCENES')+result['scene']]
score_tick = (theme_start*SECTION_STEPS*STEP_TICKS+music_tick) % symbol('MUSIC_TOTAL_TICKS')
step, phase = divmod(score_tick,STEP_TICKS)
packed = u16(assets+symbol('VOLUME_TRACK')+score_tick*2)
voices = []
for c in range(4):
    expected_period = u16(assets+symbol('SCORE')+step*16+c*4)
    instrument = u16(assets+symbol('SCORE')+step*16+c*4+2)
    volume = 0 if result['muted'] else ((packed>>(12-c*4))&15)*4
    audio = saved[f'AUD{c}']
    length, remaining, period = struct.unpack_from('>HHH',audio,4)
    loop, pointer = struct.unpack_from('>II',audio,12)
    assert audio[1] == volume == u16(state+40+c*2), (c,audio[1],volume)
    if expected_period: assert period == expected_period, (c,period,expected_period)
    if c<3 and expected_period:
        offset = struct.unpack_from('>I',memory,assets+symbol('MUSIC_INSTRUMENTS')+instrument*8)[0]
        assert loop == assets+symbol('MUSIC_SAMPLES')+offset
        assert length == 8
    if c==3:
        offset = struct.unpack_from('>I',memory,assets+symbol('MUSIC_INSTRUMENTS')+symbol('MUSIC_SILENCE')*8)[0]
        assert loop == assets+symbol('MUSIC_SAMPLES')+offset and length==1
        if remaining>1:
            sample_offset, sample_words = struct.unpack_from('>IH',memory,assets+symbol('MUSIC_INSTRUMENTS')+instrument*8)
            sample_start = assets+symbol('MUSIC_SAMPLES')+sample_offset
            assert sample_start <= pointer < sample_start+sample_words*2
            assert remaining <= sample_words
    voices.append({'channel':c,'volume':audio[1],'period':period,'instrument':instrument,
                   'loop_words':length,'remaining_words':remaining,'dma_pointer':pointer,'loop_pointer':loop})
result.update(music_tick=music_tick,theme=THEMES[step//SECTION_STEPS],step=step,phase=phase,
              paused=bool(u16(state+symbol('PAUSED'))),voices=voices)
path = ROOT/'validation/music-native.json'
history = json.loads(path.read_text()) if path.exists() else []
if not history or history[-1] != result: history.append(result)
path.write_text(json.dumps(history,indent=2)+'\n')
print(json.dumps(result,indent=2))
