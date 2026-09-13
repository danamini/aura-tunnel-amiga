# Aura Tunnel Amiga implementation plan

Status: development preview, 13 September 2026. The broad visual refinement pass
is implemented and checked in FS-UAE. Remaining work is listed below.

Target: PAL Amiga 500, normal-speed 68000, OCS, 512 KiB CHIP and 512 KiB slow RAM.
The boot demo takes over the machine. VBL interrupts preempt rendering for timing
and Paula music; AmigaOS multitasking does not run underneath it.

## Comparison brief

Preserve the [Spectrum demo's](https://github.com/danamini/aura-tunnel) ten scenes,
order, musical themes and recognisable choreography. Scene durations and rendering
can change to make the comparison readable. This is an experiment in using AI to
help create things and learn how the two machines differ. Music starts on.

## Implemented

- Bootable ADF, double-buffered planar display and VBL publication counters.
  Copper colours, blitter clearing/copying/masking and four sampled Paula voices
  provide the common rendering and sound system.
- Neon Tunnel uses deeper checker walls, half-open parity edges and one blitter
  area fill. Near walls extend beyond the viewport before wrapping. Dotted radial
  spokes and the near rim outline are removed.
- Copper Roto uses 64 precalculated checker orientations, compressed poses,
  Copper row repetition and address-based vertical movement. Rotation is prepared
  offline; the blitter has no arbitrary rotation instruction.
- Star Snake has additional orbiting cubes and comparison-focused text. Individual
  letters roll through 16 angles, with changing wave amplitude/frequency and
  moving colour. Its 15.36-second scene uses cached masks and blitter drawing.
- The central sine scroller uses 640 horizontal pixels across a 144-line band,
  masked column copies, vertical stretching, repeated rows and moving chrome
  reflections. Its message is `ZX SPECTRUM TO AMIGA / AI`. AI/ZX glyphs spin
  independently through 16 angles. Upright glyphs retain 128 source columns;
  compact rotating masks expand 32 columns through a 68000 lookup table.
  The scene uses its final display mode from entry to avoid an initial mode jump.
- Solid Cubes has a hero and eight satellites with distinct rotation phases,
  stable face materials and masked padding.
- Dot Runner lasts 15.36 seconds, with slow/fast companions and an R body/dot
  toggle. Shaded bodies retain the CMU motion. The California sunset includes
  palms, houses and independently moving ground patterns from the Spectrum.
  Opaque silhouettes place the sun behind the trees.
- Deep Space layers a galaxy, stars and an opaque planet. Two foreground meteors
  move horizontally at fixed heights and wrap outside the viewport.
- Graph plots are centred, raised and slide through a 116-line viewport clear
  of the footer. The live fixed-point calculation precedes the baked plots.
  The on-screen comparison is between implementations, not CPU speeds or two
  BASIC interpreters. See [the measurement method](graph-comparison.md).
- Night Train has a complete 104-line city image raised to y32, 52-line carriages,
  separate scrolling speeds and slow stars clipped above the skyline. R switches
  sourced artwork to the original procedural backdrop and fighter comparison.
- Mustermann and Jones use hardware sprite channels 0–2 and 4–6 with separate
  palettes and foreground priority. Their compressed banks contain 56 and 47
  poses respectively. Both use four PAL ticks per selected pose, with complete
  attacks and recoveries. A brief sweep cue waits for an active kick to finish.
  Position interpolation follows the Spectrum track at a shared half-speed clock.
- The opening screen explains the AI-assisted comparison. The HUD consistently
  shows LMB: NEXT, RMB: ON/OFF and FPS. Scene-specific R prompts and the footer
  reference the original Spectrum demo.

## Research and provenance

[Commodore's blitter manual](https://www.theflatnet.de/pub/cbm/amiga/AmigaDevDocs/hard_6.html)
informed shifting, masking and source modulo. The
[sprite manual](https://www.theflatnet.de/pub/cbm/amiga/AmigaDevDocs/hard_7.html)
informed foreground priority. The
[display reference](https://www.amigarealm.com/computing/knowledge/hardref/ch3.htm)
informed the mixed hires/lowres display. These hardware features do not imply
that every scene can render at 50 FPS.

The requested research and tunnel subagents reviewed
[Planet Rocklobster](https://github.com/AxisOxy/Planet-Rocklobster),
[subpixel blitter lines](https://github.com/Kalmalyzer/subpixel-blitter-line),
[ACE scrolling](https://github.com/AmigaPorts/ACE/blob/main/src/ace/managers/viewport/scrollbuffer.c),
[ACE sprite conversion](https://github.com/AmigaPorts/ACE/blob/main/tools/src/sprite_conv.cpp),
[Modulo Tricks](https://powerprograms.nl/amiga/modulo-tricks.html) and
[Gradient Blaster](https://github.com/grahambates/gradient-blaster).
They informed the geometry, wrapping, row reuse and palette work. No third-party
engine code was imported. HAM and a framework/music-player migration are deferred.
[Bartman's debugger](https://github.com/BartmanAbyss/vscode-amiga-debug) remains an
optional profiling tool; use strict OCS settings when configuring it.

[CREDITS](../CREDITS.md) and [fighter provenance](../assets/fighters/SOURCE.md)
record the selected artwork, music and motion sources. Packaging includes notices
beside the ADF. The three full CC0 fighter packs are archived separately under
`/Users/daniel/per-dev/reference-assets/fighters`, with source pages and SHA-256
manifests. They are not part of the demo repository or disk.

## Verification and remaining refinement

`make test` checks disk checksum/payload, pinned sources, body bounds, sprite DMA,
pose pacing, hires shifts/stretching, rotating glyphs, parallax wrap and occlusion.
`python3 validation/tunnel-geometry-check.py` checks all 128 tunnel phases for
closed parity, write bounds and nearest-wall viewport coverage.

The packaged binary is identified in [build-info.json](../dist/build-info.json).
The approved preview's SHA-256 is
`5e82bfa5d2bcf8c205b9f38038611f25707ede4c729ddca4409f0081566db921`.
FS-UAE checks confirmed the raised city, faster matched fighters and spinning
text. The [native font check](../validation/september-refinement-big-spin.json)
matched all 19,920 cached bytes, including the wrap seam. The
[fighter preview](../validation/september-refinement-fighter-tempo.json) measured
about 24 FPS. Big text measured about 19 FPS in the preceding build with the
same renderer. These are cycle-exact emulator samples, not physical-hardware
measurements or a clean uninterrupted playlist benchmark.

Outstanding work:

- Profile the large scroller's column/rotation work and recover performance while
  retaining the approved motion. Compare shaded and dot runner costs.
- Record a complete uninterrupted playlist benchmark after the final tuning,
  excluding each scene's first 40 ticks and retaining the binary hash.
- Test on physical OCS hardware.
- Improve transitions where extra background colours cannot be represented by
  the frozen two-plane image. New train art and big text enter directly.
- Resolve the closer Night Train parallax idea: foreground scenery or nearer
  stars. The current city and carriages already move independently.
- Refine airborne and sweep choreography; selected modern poses do not match
  every Spectrum move exactly, and the source packs contain unused moves.

Earlier measurements and implementation decisions are retained in
[the refinement history](refinement-history.md). Each validation JSON identifies
its own binary; older results do not describe the latest build.
