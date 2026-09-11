# Amiga Aura implementation plan

Target: PAL A500, 68000 at normal speed, OCS, 512 KiB CHIP and 512 KiB slow RAM.
The boot demo takes over the machine. VBL interrupts preempt rendering for timing
and Paula music; AmigaOS multitasking is not running underneath it.

Status: parked at Daniel's request on 11 September 2026. Resume from the
verification and refinement list below before adding effects. The Spectrum source
is https://github.com/danamini/aura-tunnel .

## Comparison brief

Keep the Spectrum demo's ten scenes, order, duration, motion and musical themes.
Make the Amiga difference visible through colour, finer lettering, shaded bodies,
richer fighter animation and layered scenery. Run the native ADF in FS-UAE.
Music starts muted at Daniel's request.

## Implemented

- Bootable 880 KiB ADF, double-buffered planar display, VBL publication and counters.
- Copper colours, blitter clearing, copying, masking and sampled Paula voices.
- Top clipping correction: publish hardware bitplane pointers before additional
  Copper patching. Updating only the already-executed Copper instructions was late.
- Native 640-pixel large-text band. Original vector outlines are resampled at
  half-pixel intervals, preserving physical letter size, speed and sine wavelength.
- Blitter squash/recover pass for the hires ribbon, with independent star motion.
  This is an expressive effect; it is not assumed to improve rendering speed.
- Roto DMA row repetition with Copper odd modulo, separate sharp dot plane and
  address-based vertical bob. Original rotation frames remain precomputed.
- Masked cube BOBs prevent transparent padding from erasing neighbouring objects.
- Three shaded runners follow the pinned CMU joints. R toggles original dots;
  the same sunset and drifting ridge remain visible, with an on-screen prompt.
- Space uses a static galaxy and shaded planet. Planet row spans reject stars
  behind the opaque disc, retaining galaxy < stars < planet depth order.
- Train skyline, lamps and rails have independent blitter sub-word scrolling.
  The distant palette is subdued to separate depth from the foreground.
- Two 48x56 fighters use six hardware sprite channels, 47 authored poses, mirrored
  double-buffered DMA data, foreground priority and interpolated Spectrum X paths.
- Live fixed-point graph calculation precedes the baked plots. It is labelled
  68000 fixed-point, not a simulated AmigaBASIC benchmark.
- Immutable emulator releases pair each disk with its symbols. Save-state tools
  reject a binary mismatch before reading counters or pointers.

## Research adopted and deferred

The user-requested OCS research subagent completed hardware and library reviews,
then reviewed the hires, parallax, keyboard, elastic text and roto approaches.

[Commodore's blitter manual](https://www.theflatnet.de/pub/cbm/amiga/AmigaDevDocs/hard_6.html)
informs shifts, masks, source modulo and cookie-cut compositing. The blitter has
no arbitrary scale or rotation command. Many tiny column blits are not inherently
faster than sparse generated 68000 painters. Current painters retain exact sine
geometry; the blitter handles the ribbon's global vertical squash.

[Display hardware](https://www.amigarealm.com/computing/knowledge/hardref/ch3.htm)
supports a one-plane 640x56 noninterlaced text band with the same display-fetch
word count as the two-plane 320-pixel band. This does not guarantee equal CPU
rendering cost. Restore both lowres bitplane pointers after the band.

[Sprite priorities](https://www.theflatnet.de/pub/cbm/amiga/AmigaDevDocs/hard_7.html)
require PF2P even for a single playfield. BPLCON2=$24 puts all fighters in front
of lights and scenery. Copper reuses their channels for meters below the stage.

[ACE scrolling](https://github.com/AmigaPorts/ACE/blob/main/src/ace/managers/viewport/scrollbuffer.c)
provided a reference for pointer, fine-scroll and wrap reasoning. Our assembly
uses duplicated strips and blitter shifts. No ACE runtime or code is imported.
[ACE's sprite converter](https://github.com/AmigaPorts/ACE/blob/main/tools/src/sprite_conv.cpp)
was a format reference; its current multiplexing limitation argues for retaining
our Copper-controlled reuse. ACE is MPL-2.0.

[Modulo Tricks](https://powerprograms.nl/amiga/modulo-tricks.html) supplies an
independent column-blitter example and explains row reuse. Its licence is MIT
text with an additional ML-training restriction. No source was copied. Benchmark
any future per-column blitter renderer before replacing exact CPU painters.

[Gradient Blaster](https://github.com/grahambates/gradient-blaster) informed the
OCS palette review. Our sunset generator uses a fixed 12-bit ramp; temporal
colour alternation is avoided because flicker was an observed problem.

[Bartman's debugger](https://github.com/BartmanAbyss/vscode-amiga-debug) remains an
optional profiling tool. Integrating its ELF/GDB workflow is deferred. Verify
strict OCS settings rather than inheriting its default ECS-Agnus A500 profile.

HAM is deferred. A moving bitmap overlay can disturb HAM's previous-pixel colour
state, while ordinary palette planes provide clean silhouettes within the budget.
A framework or music-player migration would add no necessary capability here.

## Verification and remaining refinement

`make test` checks the disk checksum and payload, pinned sources, body stream
bounds, fighter DMA layout, genuine hires columns, shifted parallax across wrap,
and planet occlusion spans. Emulator evidence remains necessary for timing.

Visual checks confirmed the runner prompt, body/dot toggle, complete upper bodies,
warmer sunset, detailed foreground fighters and restored hires header/footer.
The latest Copper roto and elastic scroller were seen running in the emulator.
The saved partial-run counters show roto about 49.8 fps, elastic hires scrolling
about 22.4 fps, and shaded runners about 24.8 fps. These are partial-cycle results,
not release benchmarks; other tested scenes were near 50 fps. The capture and
its binary hash are in `docs/validation/parked-snapshot.json`. Night Train was
visually checked in the prior build but has no final counter sample.

The final screenshots show the main footer, but the lower `AMIGA 500 / PAL` and
`FPS` labels can disappear while the numeric FPS remains. The label pixels exist
in framebuffer RAM. Compare the framebuffer with the actual display in a contemporaneous capture;
there is no established Copper, fetch or palette cause.

Keep or optimise the elastic pass only after comparing a full cycle against the
previous 25 fps hires renderer. Group consecutive source rows as well as repeated
rows, or investigate Copper resampling. The resumed blitter pass now groups both consecutive and repeated rows.
Runners also need a measured comparison of body and dot modes with ridge scrolling.

Capture a full uninterrupted playlist after the final build, including transitions.
Measure publications against independently advancing VBL ticks, excluding the
first 40 ticks of each scene. Paused/direct-selection runs are not final benchmarks.
Retain the binary hash with results. Do not infer FPS from the music clock.

The two-plane transition representation cannot reproduce every extra background
colour of the runner/space modes. Their mode boundary currently changes the static
backdrop immediately. A palette fade or full composite transition is a remaining
visual refinement. The hires/roto outgoing frames are reduced/reconstructed for
existing two-plane transitions. Do not describe these as pixel-identical fades.

Fighter travel follows the original script, with interpolated X coordinates.
Their new 47-pose sequence does not yet map every original kick/sweep cue one for
one. The existing artwork lacks exact equivalents for all six old move types.
Retain choreography as the reference when selecting additional authored poses.

## Resumed refinement, 11 September 2026

- Neon tunnel: replace isolated dots with eight-sided perspective rings drawn
  by OCS blitter line mode, bright near vertices and dashed depth rails.
- Copper roto: pack 320 independent horizontal checker pixels into the same
  40-byte source rows. Copper still repeats rows and bobs the display; there is
  no arbitrary hardware rotation instruction. Vertical resolution remains 20
  source rows and the animation retains 64 precalculated orientations.
- Hires scroll: 40-pixel lettering, an obvious 24–100% vertical elastic cycle,
  and exact sine-height runs drawn with masked, shifted blitter copies.
  Stretch programs group consecutive and repeated source rows. Independent
  shift tests cover alignment, screen edges and text wrapping.
- Runners: 768 ticks (15.36 seconds), slower left companion, labelled SLOW/FAST,
  and warm-white PRESS R: BODIES / DOTS text across both dynamic planes.
- Graph: remove deliberate throttling, measure the complete 1,363-candidate
  calculation, compare with the recorded Spectrum ROM BASIC baseline, and
  reduce the scene from 25.24 to 10.24 seconds. See graph-comparison.md.

Current direct-selection checks show tunnel 49.75 fps and the new elastic
scroller 24.97 fps. These are sampled emulator results, not a full release
benchmark. The runner prompt and speed labels were visually confirmed.
The earlier footer hypothesis about line 255 is unproven: label and numeric
pixels use the same plane and rows. Investigate a contemporaneous display/state
capture if it recurs; do not attribute it to Copper rollover without evidence.

## Chrome and geometry refinement

- Bold hires glyphs with a silver/white horizon, dark seam and blue-steel
  reflection. A 64-phase OCS colour table follows the blitter stretch; Copper
  changes COLOR01 every four display lines. No additional hires bitplane.
- Remove the unused hires CPU painter and its duplicated column index/code.
  The masked blitter bitmap renderer is now the only hires glyph path.
- Cube opposite-face pairs keep cyan, purple and gold materials. Palette
  values remain constant across scanlines; periodic rocking and scale changes
  make rotation and approach/recession visible without growing BOB footprints.
- Night Train background stars are clipped above logical row 88, the start of
  the skyline. They no longer show through the lower city and foreground.
- Graphs slide vertically using two clipped blitter rectangles. Each 128-tick
  baked slot has a 64-tick slide and 64-tick hold. The first live graph gets
  128 ticks; total graph-scene duration remains 512 ticks (10.24 seconds).
- Tunnel: ten rings, cubic depth spacing and a two-pixel vanishing radius.
  Compact two-byte vertices retain the 128-phase sequence and free CHIP RAM.
  The walls remain wireframe; filled checker walls are a further experiment,
  not implemented or claimed in this build.
- Roto: 64 independent 320×80 poses, compressed with bounded LZSS, decoded
  only when the pose changes into alternate 3,200-byte CHIP buffers. Copper
  repeats each source row twice instead of eight times: four times the vertical
  detail. All 64 pose round-trips are tested. Native decoder output was also
  compared with the generated reference in an FS-UAE save state.
- Copper footer waits remain ordered after positive roto bob. This addresses
  a concrete ordering defect, without claiming it explained every old label issue.

The first finer-roto run sampled 29.63 fps, and the deeper tunnel 24.89 fps.
These are direct-selection emulator observations. Final decoder optimisation
and its measurement are recorded separately; do not imply the entire show
runs at 50 fps. Source frame count is distinct from displayed frame rate.

Final native checks: the unrolled decoder sampled 34.18 fps over 474 VBLs,
with decoded pose 0 matching all 3,200 reference bytes. See
`validation/chrome-refinement.json` for the binary hash and counters. The graph
slide was frozen at frame 180: the published plane exactly matched the outgoing
plot cropped by 104 rows plus the incoming plot's first 104 rows. Its caption
was visually stationary; evidence is in `validation/graph-slide.json`.
Chrome lettering, stable cube materials and the clear lower Night Train skyline
were visually checked. These remain emulator checks, not physical hardware tests.
