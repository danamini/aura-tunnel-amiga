#!/usr/bin/env python3
"""Check baked tunnel coordinates against the native Q6 parity-edge raster.

This checks generated data and modeled write addresses, not emulator execution
or FPS. Source and asset hashes bind the report to the inspected build.
"""
import hashlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]


def trunc_div(numerator, denominator):
    """68000 DIVS truncates toward zero, unlike Python's negative //."""
    return (abs(numerator) // denominator) * (-1 if numerator < 0 else 1)


def main():
    data = (ROOT / 'build/assets.bin').read_bytes()
    metadata = json.loads((ROOT / 'build/assets.json').read_text())

    def asset(name):
        entry = metadata[name]
        return data[entry['offset']:entry['offset'] + entry['size']]

    tunnel = asset('TUNNEL')
    indices = [item[0] for item in struct.iter_unpack('>I', asset('TUNNEL_INDEX'))]
    assert len(indices) == 128, 'Native renderer masks phase to 127'
    assert indices[0] == 0
    ends = indices[1:] + [len(tunnel)]
    samples = []
    min_write, max_write = 10240, 0
    max_q6 = 0
    for phase, (start, end) in enumerate(zip(indices, ends)):
        assert end - start == 200, 'Native renderer expects ten 20-byte rings'
        rings = []
        for offset in range(start, end, 20):
            vertices = [(tunnel[offset + 2 + i * 2] * 2,
                         tunnel[offset + 3 + i * 2]) for i in range(9)]
            assert vertices[0] == vertices[-1], (phase, 'ring closure')
            assert all(0 <= x <= 318 and 26 <= y <= 198 for x, y in vertices)
            rings.append(vertices)
        assert {(0, 26), (318, 26), (0, 198), (318, 198)} <= set(rings[-1]), (
            phase, 'nearest ring does not cover viewport before recycling')
        crossings = [set() for _ in range(128)]
        count = 0
        for ring in range(3, 9):
            for sector in range(8):
                if (sector + ring + phase * 10 // 128) & 1:
                    continue
                quad = [rings[ring][sector], rings[ring][sector + 1],
                        rings[ring + 1][sector + 1], rings[ring + 1][sector]]
                quad = [(x, y // 2) for x, y in quad]
                for (x0, y0), (x1, y1) in zip(quad, quad[1:] + quad[:1]):
                    if y0 == y1:
                        continue
                    if y0 > y1:
                        x0, y0, x1, y1 = x1, y1, x0, y0
                    step = trunc_div((x1 - x0) * 64, y1 - y0)
                    assert -32768 <= step <= 32767, 'DIVS word overflow'
                    position = x0 * 64 + step // 2 + 32
                    for y in range(y0, y1):
                        assert -32768 <= position <= 32767, 'Q6 word overflow'
                        max_q6 = max(max_q6, abs(position))
                        x = position // 64
                        assert 0 <= x < 320 and 13 <= y < 99, (phase, x, y)
                        # Both BChg writes must remain inside the blitter's
                        # fill rectangle: display rows 26 through 197.
                        for display_y in (y * 2, y * 2 + 1):
                            address = display_y * 40 + x // 8
                            assert 26 * 40 <= address < 198 * 40
                            min_write = min(min_write, address)
                            max_write = max(max_write, address)
                        crossings[y].symmetric_difference_update([x])
                        position += step
                        count += 1
        assert all(len(row) % 2 == 0 for row in crossings), (phase, 'open fill parity')
        assert count > 0, (phase, 'empty raster check')
        samples.append(count)
    report = {
        'scope': 'Generated geometry and modeled native Q6 writes; not runtime FPS',
        'assets_sha256': hashlib.sha256(data).hexdigest(),
        'renderer_sha256': hashlib.sha256((ROOT / 'src/tunnel_fill.asm').read_bytes()).hexdigest(),
        'frames_checked': len(indices),
        'all_nearest_rings_cover_viewport_corners': True,
        'all_parity_rows_closed': True,
        'all_writes_inside_fill_rectangle': True,
        'all_q6_values_fit_signed_word': True,
        'plane_relative_write_byte_range': [min_write, max_write],
        'maximum_sampled_q6_magnitude': max_q6,
        'edge_samples_per_frame': {'minimum': min(samples), 'maximum': max(samples),
                                   'mean': sum(samples) / len(samples)},
    }
    output = ROOT / 'validation/tunnel-geometry-check.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
