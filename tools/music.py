"""Load the pinned MOD conversion and independently decode its Paula events."""
from pathlib import Path
import struct
import math
import wave

ROOT = Path(__file__).resolve().parents[1]
PAL_CLOCK = 3546895


class Music:
    def __init__(self, score, bank):
        self.score, self.bank = score, bank
        assert score[:4] == b'LSP1' and score[4:8] == bank[:4]
        version, flags, bpm, self.rewind, self.tempo, self.position = struct.unpack_from('>6H', score, 8)
        assert version == 0x11f and flags == 0 and bpm == 125
        self.ticks = struct.unpack_from('>I', score, 20)[0]
        count = struct.unpack_from('>H', score, 24)[0]
        p = 26
        self.instruments = []
        for _ in range(count):
            start, size, loop, repeat = struct.unpack_from('>IHIH', score, p)
            assert size and repeat and start % 2 == loop % 2 == 0
            assert start + size * 2 <= len(bank) and loop + repeat * 2 <= len(bank)
            self.instruments.append((start, size, loop, repeat))
            p += 12
        count = struct.unpack_from('>H', score, p)[0]
        p += 2
        self.codes = struct.unpack_from(f'>{count}H', score, p)
        p += count * 2
        assert struct.unpack_from('>H', score, p)[0] == 0, 'No sequence-seeking table expected'
        p += 2
        words, bloop, wloop = struct.unpack_from('>III', score, p)
        self.word_start = p + 12
        self.byte_start = self.word_start + words
        self.byte_loop = self.byte_start + bloop
        self.word_loop = self.word_start + wloop

    def frames(self, count=None):
        """Yield register values after each tick, plus retriggers and stream offsets."""
        b, w = self.byte_start, self.word_start
        volumes, periods = [0] * 4, [0] * 4
        pointers, lengths = [0] * 4, [1] * 4
        repeats = [None] * 4
        for tick in range(self.ticks if count is None else count):
            while True:
                code = 0
                while True:
                    value = self.score[b]
                    b += 1
                    code += value
                    if value:
                        break
                    code += 256
                command = self.codes[code]
                if command == self.rewind:
                    b, w = self.byte_loop, self.word_loop
                    continue
                assert command not in (self.tempo, self.position), 'Unexpected tempo/position command'
                break
            for c in range(3, -1, -1):
                if command & (1 << (c + 4)):
                    volumes[c] = self.score[b]
                    b += 1
                    assert 0 <= volumes[c] <= 64
            for c in range(3, -1, -1):
                if command & (1 << c):
                    periods[c] = struct.unpack_from('>H', self.score, w)[0]
                    w += 2
            instrument, dma = -12, 0
            for c in range(3, -1, -1):
                op = (command >> (8 + c * 2)) & 3
                if op == 1:
                    assert repeats[c] is not None
                    pointers[c], lengths[c] = repeats[c]
                elif op >= 2:
                    instrument += struct.unpack_from('>h', self.score, w)[0]
                    w += 2
                    assert instrument % 6 == 0
                    index, half = divmod(instrument, 12)
                    assert op != 3 or half == 0
                    desc = self.instruments[index]
                    pointers[c], lengths[c] = desc[:2]
                    # Half-instrument offsets address the loop descriptor at byte +6.
                    if half:
                        pointers[c], lengths[c] = desc[2:]
                        repeats[c] = self.instruments[index + 1][:2]
                    else:
                        repeats[c] = desc[2:]
                    instrument += 6
                    if op == 3:
                        dma |= 1 << c
            yield {'tick': tick, 'volumes': tuple(volumes), 'periods': tuple(periods),
                   'pointers': tuple(pointers), 'lengths': tuple(lengths), 'dma': dma,
                   'byte_offset': b, 'word_offset': w}


def bake():
    directory = ROOT / 'assets/music'
    music = Music((directory / 'robotsound.lsmusic').read_bytes(),
                  (directory / 'robotsound.lsbank').read_bytes())
    return {'MUSIC_SAMPLES': music.bank}, music


def preview(path, music):
    """Render PCM and return four packed sample-peak meters per PAL tick."""
    rate = 22050
    signed = [b if b < 128 else b - 256 for b in music.bank]
    position, start, size, active = [0.] * 4, [0] * 4, [2] * 4, [False] * 4
    levels, envelopes = bytearray(), [0] * 4
    with wave.open(str(path), 'wb') as output:
        output.setparams((2, 2, rate, 0, 'NONE', 'not compressed'))
        for frame in music.frames():
            for c in range(4):
                if frame['dma'] & (1 << c):
                    start[c], size[c] = frame['pointers'][c], frame['lengths'][c] * 2
                    position[c], active[c] = 0., True
            step = [PAL_CLOCK / max(124, p) / rate if p else 0 for p in frame['periods']]
            pcm = bytearray()
            peaks = [0] * 4
            for _ in range(rate // 50):
                values = [0] * 4
                for c in range(4):
                    if not active[c]:
                        continue
                    while position[c] >= size[c]:
                        position[c] -= size[c]
                        start[c], size[c] = frame['pointers'][c], frame['lengths'][c] * 2
                    values[c] = signed[start[c] + int(position[c])] * frame['volumes'][c] * 2
                    peaks[c] = max(peaks[c], abs(values[c]))
                    position[c] += step[c]
                pcm.extend(struct.pack('<hh', values[0] + values[3], values[1] + values[2]))
            output.writeframesraw(pcm)
            # Square-root response makes quiet instruments visible. Fast attack,
            # 160 ms maximum fall, including the silent tail of one-shot samples.
            for c in range(4):
                peak = min(15, math.isqrt(peaks[c] * 225 // 16256))
                envelopes[c] = max(peak, envelopes[c] - 2)
            levels.extend(struct.pack('>H', sum(v << (12-c*4) for c,v in enumerate(envelopes))))
    return bytes(levels)
