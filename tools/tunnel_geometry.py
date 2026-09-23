"""Compact, bending dodecagonal tunnel shared by assets and validation."""
import math
import struct

SECTORS = 12
RINGS = 10
FIRST_FILLED_RING = 5
PHASE_BITS = 6
PHASES = 1 << PHASE_BITS
TICKS_PER_POSE_BITS = 1
RING_BYTES = 2 + (SECTORS + 1) * 2
FRAME_BYTES = RING_BYTES * RINGS


def pose(frame):
    phase = frame * math.tau / PHASES
    depths = sorted(((ring / RINGS + frame / PHASES) % 1)
                    for ring in range(RINGS))
    result = []
    for depth in depths:
        radius = 2 + 70 * depth * depth / (1 - depth)
        cx = 160 + 24 * math.sin(phase + depth * 2.7)
        cy = 112 + 12 * math.cos(phase * 2 + depth * 3)
        twist = phase + depth * (.6 + .45 * math.sin(phase))
        vertices = []
        for sector in range(SECTORS):
            theta = sector * math.tau / SECTORS
            # Three rounded lobes, varying along the tunnel's length.
            r = radius * (1 + .12 * math.sin(theta * 3 + depth * 2 + phase * 2))
            x = max(0, min(318, round(cx + r * math.cos(theta + twist))))
            y = max(26, min(198, round(cy + r * .54 * math.sin(theta + twist))))
            vertices.append((x // 2 * 2, y))
        style = 2 if depth < .35 else 3 if depth > .8 else 1
        result.append((style, vertices))
    return result


def generate():
    data = bytearray()
    indices = []
    for frame in range(PHASES):
        indices.append(len(data))
        for style, vertices in pose(frame):
            data.extend(struct.pack('>H', style))
            data.extend(v for x, y in vertices + [vertices[0]] for v in (x // 2, y))
    assert len(data) == PHASES * FRAME_BYTES
    return indices, data


def constants():
    return {'TUNNEL_SECTORS': SECTORS, 'TUNNEL_RINGS': RINGS,
            'TUNNEL_PHASE_BITS': PHASE_BITS, 'TUNNEL_PHASES': PHASES,
            'TUNNEL_TICK_SHIFT': TICKS_PER_POSE_BITS,
            'TUNNEL_RING_BYTES': RING_BYTES,
            'TUNNEL_FIRST_FILLED_RING': FIRST_FILLED_RING}
