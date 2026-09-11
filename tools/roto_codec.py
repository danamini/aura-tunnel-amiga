"""Independent checker poses and a small, bounded 68000-friendly LZSS codec.

Each group starts with eight low-bit-first token flags: 1 means a literal byte;
0 means a big-endian pair containing (distance-1)<<4 | (length-3).
Distances are 1..4096 and lengths 3..18. Each pose starts a fresh dictionary.
"""
import collections
import math
import struct


def encode(data):
    data = bytes(data)
    out = bytearray()
    chains = collections.defaultdict(list)
    pos = 0
    while pos < len(data):
        flags = 0
        tokens = bytearray()
        for bit in range(8):
            if pos == len(data):
                break
            length = distance = 0
            for previous in reversed(chains[data[pos:pos + 3]][-64:]):
                offset = pos - previous
                if offset > 4096:
                    break
                count = 3
                while count < 18 and pos + count < len(data) and data[previous + count] == data[pos + count]:
                    count += 1
                if count > length:
                    length, distance = count, offset
                if count == 18:
                    break
            if length >= 3:
                tokens.extend(struct.pack('>H', ((distance - 1) << 4) | (length - 3)))
            else:
                flags |= 1 << bit
                tokens.append(data[pos])
                length = 1
            for previous in range(pos, pos + length):
                chains[data[previous:previous + 3]].append(previous)
            pos += length
        out.append(flags)
        out.extend(tokens)
    return bytes(out)


def decode(data, size):
    """Reject truncated, overlong, backward-out-of-bounds and trailing streams."""
    if size < 0:
        raise ValueError('negative output size')
    out = bytearray()
    pos = 0
    while len(out) < size:
        if pos >= len(data):
            raise ValueError('missing flags')
        flags = data[pos]
        pos += 1
        for bit in range(8):
            if len(out) == size:
                break
            if flags & (1 << bit):
                if pos >= len(data):
                    raise ValueError('missing literal')
                out.append(data[pos])
                pos += 1
            else:
                if pos + 2 > len(data):
                    raise ValueError('missing match')
                token = int.from_bytes(data[pos:pos + 2], 'big')
                pos += 2
                distance, count = (token >> 4) + 1, (token & 15) + 3
                if distance > len(out) or len(out) + count > size:
                    raise ValueError('match outside output bounds')
                for _ in range(count):
                    out.append(out[-distance])
    if pos != len(data):
        raise ValueError('trailing input')
    return bytes(out)


def checker_pose(frame, frames=64, rows=80):
    """320 horizontal samples, 160-line scene extent and original rotation."""
    angle = frame * math.tau / frames
    pitch = 38 + 12 * math.sin(angle)
    cosine, sine = math.cos(angle), math.sin(angle)
    out = bytearray()
    for row in range(rows):
        y = row * 160 / rows - 80
        pixels = [(math.floor(((x - 160) * cosine + y * sine) / pitch)
                   + math.floor((-(x - 160) * sine + y * cosine) / pitch)) & 1
                  for x in range(320)]
        out.extend(sum(pixels[x + b] << (7 - b) for b in range(8))
                   for x in range(0, 320, 8))
    return bytes(out)


def generate(frames=64, rows=80):
    """Return offsets (with terminal end offset) and independently coded poses."""
    offsets = [0]
    payload = bytearray()
    for frame in range(frames):
        raw = checker_pose(frame, frames, rows)
        compressed = encode(raw)
        assert decode(compressed, len(raw)) == raw
        payload.extend(compressed)
        offsets.append(len(payload))
    return offsets, bytes(payload)


def self_test():
    import random
    rng = random.Random(500)
    samples = [b'', b'A', bytes(3200), bytes(range(256)) * 20,
               bytes(rng.randrange(256) for _ in range(7000))]
    for sample in samples:
        assert decode(encode(sample), len(sample)) == sample
    for data, size in [(b'', 1), (b'\x01', 1), (b'\x00\x00', 3),
                       (b'\x00\x00\x00', 3), (b'\x01A\x00\x0f', 5),
                       (b'\x01AB', 1), (b'', -1)]:
        try:
            decode(data, size)
        except ValueError:
            pass
        else:
            raise AssertionError((data, size))
    offsets, payload = generate()
    for frame in range(64):
        assert decode(payload[offsets[frame]:offsets[frame + 1]], 3200) == checker_pose(frame)
    print(f'64 poses: {len(payload)} compressed bytes; {len(offsets) * 4} index bytes; all codec checks passed')


if __name__ == '__main__':
    self_test()
