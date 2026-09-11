# Graph implementation comparison

The earlier Amiga graph deliberately evaluated only two candidates per rendered
frame for 15 seconds. That was presentation pacing, not a speed benchmark.
The native calculation now runs all 1,363 candidates immediately, including its
buffer and horizon initialisation, and holds the result for 2.56 seconds from
scene entry. Three precalculated plots follow in 2.56-second slots, each with
a 1.28-second vertical slide and a 1.28-second hold.

The Spectrum baseline is the corrected standalone ROM BASIC benchmark from
[Aura Tunnel](https://github.com/danamini/aura-tunnel): 557,027,926 contended
48K Z80 T-states, or 159.150836 simulated seconds at 3.5 MHz, including DIM/setup
and excluding loading. Its result is retained in `validation/spectrum-basic-baseline.json`.
Both evaluate X=0..140 step 3 and Y=0..140 step 5: 47 × 29 = 1,363 candidates.
A candidate need not produce a visible pixel.

The Amiga measures elapsed PAL VBL interrupts around the complete native job.
It adds one tick to round conservatively upward; resolution is 20 ms. The first
strict A500/OCS emulator capture measured 19 ticks, displayed as 380 ms and an
approximate 418× implementation speed-up. The displayed ratio is calculated
from the measured ticks on each scene entry, not a hardcoded speed claim.
`validation/graph-comparison.json` identifies the captured binary and completed
loop state (X=0, Y=145). Timing is emulated, not physical-hardware evidence.

This compares two implementations, not CPU speed or equivalent BASIC interpreters.
Sinclair ROM BASIC uses floating-point EXP and interpreter overhead. The Amiga
uses native 68000 instructions, Q14 arithmetic, eight repeated squarings to
approximate EXP, and 181/256 for COS(PI/4). Projection and indexing are quantised;
the display is half-height, as in the Spectrum live preview. BASIC's unconditional
horizon update is preserved. The outputs need not be pixel-identical.
An actual Amiga BASIC comparison would require running that interpreter with
the same program and timing rules; this preview does not claim to do that.
