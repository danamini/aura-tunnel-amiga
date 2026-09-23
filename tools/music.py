"""Offline four-voice Paula arrangement and a preview of the baked DMA score."""
import math
import random
import struct
import wave

PAL_CLOCK = 3546895
WAVE_SIZE = 16
STEP_TICKS = 10
SECTION_STEPS = 64
SCENE_THEMES = (0, 1, 2, 3, 1, 2, 0, 3, 2, 1)
THEMES = ('Korobeiniki', 'Neon Drive', 'Ode to Joy', 'Night Flight')


def pitch(note):
    semitone = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}[note[0]]
    return 12 * (int(note[-1]) + 1) + semitone + ('#' in note)


def period(midi):
    return round(PAL_CLOCK / (WAVE_SIZE * 440 * 2 ** ((midi - 69) / 12)))


def pcm(values):
    return bytes(max(-127, min(127, round(v))) & 255 for v in values)


def arrange(score):
    # Full 16-sample cycles: even C6 stays above Paula's PAL DMA period limit.
    waves = [pcm(fn(i * math.tau / WAVE_SIZE) for i in range(WAVE_SIZE)) for fn in (
        lambda t: 92 * (2 / math.pi) * math.asin(math.sin(t)),
        lambda t: 66 * math.sin(t) + 25 * math.sin(2*t) + 12 * math.sin(3*t),
        lambda t: 76 * math.sin(t) + 28 * math.sin(3*t),
        lambda t: 68 * math.sin(t) + 26 * math.cos(2*t) + 15 * math.sin(4*t),
        lambda t: 112 * math.sin(t),
        lambda t: 88 * math.sin(t) + 24 * math.sin(2*t),
        lambda t: 64 * math.sin(t) + 30 * math.sin(4*t),
        lambda t: 55 * math.sin(t) + 22 * math.sin(3*t) + 20 * math.sin(5*t),
    )]
    rng = random.Random(500)
    kick = pcm(120 * math.exp(-i/135) * math.sin(2*math.pi*(i*.010 + .9*(1-math.exp(-i/35)))) for i in range(512))
    snare = pcm((rng.uniform(-95,95) + 30*math.sin(i*.19))*math.exp(-i/120) for i in range(512))
    hat = pcm(rng.uniform(-110,110)*math.exp(-i/25) for i in range(128))
    tom = pcm(115*math.exp(-i/120)*math.sin(i*.08 + .8*(1-math.exp(-i/30))) for i in range(512))
    samples = waves + [kick, snare, hat, tom, bytes(2)]
    notes, envelopes = [], []
    for step, note in enumerate(score.MELODY):
        section, local = divmod(step, SECTION_STEPS)
        beat, phrase = local % 16, local // 16
        root = pitch(score.BASS[step//8])
        # Alternating octaves and pickups, with a different groove per theme.
        bass_active = beat % 2 == 0 or (section in (1,3) and beat in (7,11,15))
        bass = root + (12 if beat in (6,14) else 0)
        third = 4 if section == 2 or score.BASS[step//8][0] in 'CFG' else 3
        arp_pattern = ((0,7,12,third), (0,third,7,12), (7,12,third,0), (12,7,third,7))[section]
        arp = root + 24 + arp_pattern[(local+phrase)%4]
        arp_active = section != 2 or local % 4 != 3
        drum = 8 if beat in ((0,8) if section == 2 else (0,6,8)) else 9 if beat in (4,12) else 10
        if beat >= 14 and phrase % 2 == 1:
            drum = 11 if beat == 14 else 9
        drum_active = section != 2 or beat % 2 == 0
        drum_period = {8:428,9:320,10:190,11:390}[drum]
        voices = [(period(pitch(note)) if note else 0, section),
                  (period(bass) if bass_active else 0, 4+(section%2)),
                  (period(arp) if arp_active else 0, 6+(section%2)),
                  (drum_period if drum_active else 0, drum)]
        notes.append(voices)
        for phase in range(STEP_TICKS):
            lead = (12,14,13,12,11,10,9,7,4,0)[phase] if note else 0
            bass_v = (15,14,12,10,8,6,4,2,0,0)[phase] if bass_active else 0
            arp_v = (9,10,8,6,4,3,2,0,0,0)[phase] if arp_active else 0
            # Drum PCM decays to silence; these envelopes also drive the meters.
            drum_v = ((15,10,5,0,0,0,0,0,0,0) if drum != 10 else (9,0,0,0,0,0,0,0,0,0))[phase] if drum_active else 0
            envelopes.append((lead,bass_v,arp_v,drum_v))
    return samples, notes, envelopes


def bake(score):
    samples, notes, envelopes = arrange(score)
    data, descriptors = bytearray(), []
    for sample in samples:
        descriptors.append(struct.pack('>IHH',len(data),len(sample)//2,0))
        data.extend(sample)
    return {'MUSIC_SCENES':bytes(SCENE_THEMES),
            'MUSIC_INSTRUMENTS':b''.join(descriptors), 'MUSIC_SAMPLES':bytes(data),
            'SCORE':b''.join(struct.pack('>HH',*voice) for row in notes for voice in row),
            'VOLUME_TRACK':b''.join(struct.pack('>H',sum(v << (12-4*c) for c,v in enumerate(row))) for row in envelopes)}, (samples,notes,envelopes)


def preview(path, arrangement):
    """Render the same periods, PCM and 50 Hz envelopes; not an emulator capture."""
    samples, notes, envelopes = arrangement
    signed = [[b if b<128 else b-256 for b in sample] for sample in samples]
    rate = 22050
    positions = [0.] * 4
    output = bytearray()
    for tick, volumes in enumerate(envelopes):
        voices = notes[tick//STEP_TICKS]
        if tick % STEP_TICKS == 0: positions[3] = 0
        for _ in range(rate//50):
            values = []
            for c, ((per, instrument), volume) in enumerate(zip(voices, volumes)):
                sample = signed[instrument]
                pos = int(positions[c])
                value = sample[pos%len(sample)] if c<3 or pos<len(sample) else 0
                values.append(value * volume / 15 if per else 0)
                if per: positions[c] += PAL_CLOCK/per/rate
            # Paula stereo placement with light crossfeed for headphones.
            left, right = values[0]+values[3], values[1]+values[2]
            output.extend(struct.pack('<hh',round((left+.25*right)*78),round((right+.25*left)*78)))
    with wave.open(str(path),'wb') as wav:
        wav.setparams((2,2,rate,0,'NONE','not compressed'))
        wav.writeframes(output)
