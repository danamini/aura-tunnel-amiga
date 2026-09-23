# Aura Tunnel Amiga implementation plan

Status: Amiga v1.2, 23 September 2026. The robotsound soundtrack, sample-driven
HUD meters, and visual and performance refinement pass are implemented.

Target: PAL Amiga 500, normal-speed 68000, OCS, 512 KiB CHIP and 512 KiB slow RAM.
The boot demo takes over the machine. VBL interrupts preempt rendering for timing
and Paula music; AmigaOS multitasking does not run underneath it.

## Comparison brief

Preserve the [Spectrum demo's](https://github.com/danamini/aura-tunnel) ten scenes,
order and recognisable choreography. The Amiga now uses its own selected MOD soundtrack. Scene durations and rendering
can change to make the comparison readable. This is an experiment in using AI to
help create things and learn how the two machines differ. Music starts on.

## Implemented

- Bootable ADF, double-buffered planar display and VBL publication counters.
  Copper colours, blitter clearing/copying/masking and four sampled Paula voices
  provide the common rendering and sound system.
- Neon Tunnel has twelve facets, four near checker bands, a three-lobed cross-section,
  a moving vanishing point and depth-dependent twist. Four illuminated rails
  follow the middle depths, with travelling Copper colour bands. Half-open
  parity edges and one blitter area fill keep the walls closed; near walls
  extend beyond the viewport before wrapping. Geometry advances every two
  PAL ticks through 64 poses, fitting the 25 FPS renderer cadence.
- Copper Roto uses 64 precalculated checker orientations, compressed poses,
  Copper row repetition and address-based vertical movement. Rotation is prepared
  offline; the blitter has no arbitrary rotation instruction. The galaxy behind
  it makes full counterclockwise turns while the foreground spins clockwise.
  Sixteen full-width masks supply 32 angles by reversing the second half-turn.
- Star Snake has additional orbiting cubes and comparison-focused text. Individual
  letters roll through 16 angles, with changing wave amplitude/frequency and
  moving colour. Its 15.36-second scene uses cached masks and blitter drawing.
- The central sine scroller uses 640 horizontal pixels across a 144-line band,
  masked column copies, vertical stretching, repeated rows and moving chrome
  reflections. Its message is `ZX SPECTRUM TO AMIGA / AI`. Eight glyph families
  spin independently through 16 angles. Upright and rotating glyphs retain
  128 source columns, with compressed masks decoded into the font cache.
  The scene uses its final display mode from entry to avoid an initial mode jump.
- Solid Cubes has a large bobbing cube and six orbiting satellites drawn from
  rectangular boxes, octahedra, tetrahedra and triangular prisms. Three sizes,
  opposing tumble directions, a starfield and moving Copper colour reflections
  give the scene more variety. Cached poses use masked padding.
- Dot Runner lasts 15.36 seconds, with slow/fast companions and an R body/dot
  toggle. Shaded bodies retain the CMU motion. The California sunset includes
  palms, houses and independently moving ground patterns from the Spectrum.
  Opaque silhouettes place the sun behind the trees.
- Deep Space layers a galaxy, stars and an opaque planet around a rotating
  orbital reactor with three depth-sorted hoops, docking arms, a pulsing core and
  moving beacons. Two foreground meteors cross the scene. Its duration is now
  10.24 seconds, bringing the full playlist to 128 seconds.
- Graph plots are centred, raised and slide through a 116-line viewport clear
  of the footer. The live fixed-point calculation precedes the baked plots.
  The on-screen comparison is between implementations, not CPU speeds or two
  BASIC interpreters. See [the measurement method](graph-comparison.md).
- Night Train has a complete 104-line city image raised to y32, 52-line carriages,
  separate scrolling speeds and slow stars clipped above the skyline. R switches
  sourced artwork to the original procedural backdrop and fighter comparison.
  The near carriage advances one source pixel per four VBLs; the city remains
  slower. Fighters retain fixed carriage-relative roots and share its bounce.
- Mustermann and Jones use hardware sprite channels 0–2 and 4–6 with separate
  palettes and foreground priority. Their compressed banks contain 56 and 47
  poses respectively. Both use four PAL ticks per selected pose, with complete
  attacks and recoveries. A brief sweep cue waits for an active kick to finish.
  Position interpolation follows the Spectrum track at a shared half-speed clock.
- The opening screen explains the AI-assisted comparison. The HUD consistently
  shows LMB: NEXT, RMB: ON/OFF and FPS. Scene-specific R prompts and the footer
  reference the original Spectrum demo.

## 23 September refinement

- The first roto refinement placed the galaxy/planet artwork behind transparent
  checker cells, decoded once into scratch RAM and read directly by display DMA.
  The later backdrop animation below replaces that static cache.
- Night Train adds 16 fast tumbling leaves at independent speeds, stronger
  carriage/fighter bounce and a deck that follows the same movement. Jones has
  a pre-mirrored compressed bank, removing the live per-word mirror in new-art
  mode. Original artwork remains available with R.
- Eight big-letter families rotate through 128 poses, with a shorter rest and
  faster rotation cadence. Only visible letters update. Sine heights use paired
  rows: the offline model drops mean blitter groups from 80.75 to 40.875 without
  changing amplitude. This work count is separate from runtime FPS.
- Chrome now uses 36 independently animated raster colours rather than 18,
  with crossing reflections and a travelling hue wave.
- Four live Paula volume bars occupy the HUD's left compartment, replacing
  the repeated A500 label. Mouse pull-ups are initialized on takeover; M provides a keyboard music
  toggle using the [Amiga raw-key map](https://wiki.amigaos.net/wiki/Keymap_Library).
- Music envelopes retain all source values in 5,120 bytes instead of 20,480;
  phase indexing now uses all ten envelope frames in each note.
  Cube poses use a compressed bank and a scratch cache. The incoming working
  copy exceeded the CHIP allocation guard; these savings make the additions fit.

The first refinement's [playlist capture](../validation/spark-final-playlist.json) identifies
binary `ad118c17fc8e6ba3dd30a3dbc6b7ccad37657052f5ce11386cb865d86a16a584`.
Cycle-exact FS-UAE samples, excluding each scene's first 40 ticks, measured
36.26 FPS for roto, 20.37 for big text and 24.95 for train. The
[previous runnable build](../validation/spark-baseline.json) measured 33.76,
19.06 and 24.95 respectively; the incoming uncommitted build itself exceeded
its memory guard. These are emulator samples, not physical-hardware results.
Other scenes retained their approximately 25 or 50 FPS rates. The
[native font check](../validation/spark-big-spin-native.json) matched all
19,920 cached bytes, including the wrap seam. `make package` passed for that build, whose CHIP allocation was 481,280
bytes against the 483,328-byte build guard. The subsequent tunnel update is
recorded below.

## Expanded tunnel follow-up

The tunnel now uses twelve facets rather than eight, with a three-lobed
cross-section, a wandering centre and depth-dependent torsion. Four bright
rails connect the middle rings; travelling neon colours sweep the wall panels.
Four near checker bands carry the filled detail, while the distant core uses
outlines. Geometry uses 64 poses at two ticks per pose, retaining the existing
128-tick travel cycle with less asset storage.

After the opening transition, only rows 24–199 need clearing. The opaque
header, footer and HUD copies refresh their own areas. Both buffers receive
full clears through tick 40 before this optimization starts. The generator
exports the facet count, pose count and ring stride to the assembler, and the
geometry validator imports those same definitions.

`make test` passes. The [geometry check](../validation/tunnel-complex-geometry.json)
verifies all 64 poses for closed parity, viewport coverage and bounded Q6 writes.

The [native tunnel capture](../validation/tunnel-complex-final.json) measured
24.89 FPS across the complete scene, versus 24.95 FPS in the preceding preview.
The final binary is `14d5dc49d7efd07a600099ced5e6e6c9bef101bcbabbdf45ca088edaf0abf472`;
CHIP allocation is 473,600 bytes, 7,680 bytes below the preceding preview.
These are cycle-exact FS-UAE measurements; physical-hardware validation remains.

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
graphics engine code was imported. The later MOD update imports the credited
Light Speed Player. HAM and a graphics framework migration remain deferred.
[Bartman's debugger](https://github.com/BartmanAbyss/vscode-amiga-debug) remains an
optional profiling tool; use strict OCS settings when configuring it.

[CREDITS](../CREDITS.md) and [fighter provenance](../assets/fighters/SOURCE.md)
record the selected artwork, music and motion sources. Packaging includes notices
beside the ADF. The three full CC0 fighter packs are archived separately under
`/Users/daniel/per-dev/reference-assets/fighters`, with source pages and SHA-256
manifests. They are not part of the demo repository or disk.

## Earlier four-channel arrangement, 23 September 2026

This section records the v1.1 arrangement, superseded by the robotsound update
below. Its saved measurements are retained as historical evidence.

`tools/music.py` arranges the four pinned melodies for independent lead, bass,
arpeggio and percussion voices. Eight complete 16-sample tonal waveforms replace
the previously truncated loops. Kick, snare, hi-hat and tom are deterministic
one-shot PCM samples. Drum DMA restarts at note boundaries, then reloads a two-byte
silent loop after Agnus has latched the sample. The timing follows the
[audio state machine](https://amigadev.elowar.com/read/ADCD_2.1/Hardware_Manual_guide/node00F2.html).

Scene selection chooses a starting theme; the audio clock advances to the next
theme every 640 PAL ticks, independently of rendering and scene pause. Each theme
has its own lead instrument, bass rhythm and arpeggio order, with fills every
second phrase. Four packed envelopes drive both Paula and the HUD levels. M mutes
all channels while the arrangement continues. The generated 51.2-second stereo
WAV previews the same notes and samples; it does not emulate analogue filtering.

`make test` checks sample bounds, full waveform cycles, melody pitch error below
seven cents, distinct voice envelopes, four drum instruments and scene mapping.
`validation/music-native-check.py` checks FS-UAE's actual AUD0–AUD3 registers
against the immutable launched score. The saved observations in
[music-native.json](../validation/music-native.json) cover all four themes,
scene selection, progression within the scroller, mute, and an active kick DMA
buffer followed by the silent loop. One observation has volumes 48/60/36/60;
the drum still has 176 sample words left while its reload length is one word.
Music also continued while the scene was paused.

For binary `30fb7a3737befdbd584d7a611c36f6dadd63c497005479070b595d2d822327d1`,
the unpaused samples measured 24.89 FPS in the tunnel and 20.60 FPS in the scroller.
The preceding tunnel build measured 24.89 FPS; these are cycle-exact FS-UAE
measurements, not hardware measurements. The payload is 472,990 bytes and the
CHIP allocation is 477,184 bytes, below the 472 KiB project ceiling.

## Sharper big-scroll rotations, 23 September 2026

Rotating glyphs now use complete 128×40 masks, replacing 32×40 masks stretched
four times horizontally. Rotations are filtered in square-pixel space before
sampling the hires display grid, preserving the existing physical proportions.
Upright glyphs already used 128 columns; their resolution is unchanged. The
40 source rows still use the existing Copper line doubling.
[Before and after](../validation/hires-big-scroll-comparison.png) shows the same
four letter poses at identical display size.

The larger pose bank adds 8,888 bytes. Removing the expansion table saves 1,024
bytes, and compressing the stretch programs saves another 2,776. Stretch programs
decode once per scene into the unused tail of the mask buffer, beyond the blitter
column masks. The final CHIP allocation is 482,304 bytes, within the 472 KiB ceiling.

`make test` checks that diagonal poses contain independent sub-block edges and
valid compressed masks. The [native check](../validation/hires-big-spin-native.json)
verified all 19,920 font-cache bytes, including the wrap seam, and all 5,262 decoded
stretch bytes after rendering. Binary
`4bb999467f4b75ba6fdcca824b94040b1cd682ea3aec7c418312b4052524ae87`
measured 20.04 FPS over 1,417 scroller VBLs in cycle-exact FS-UAE, compared with
20.60 FPS before the resolution change. Physical-hardware validation remains open.

## Deep Space centrepiece, 23 September 2026

`tools/space_reactor.py` generates sixteen 96×96 reactor poses. Two compressed
colour planes decode into GRAPHBUF only when the pose changes; the 68000 derives
the silhouette with a longword OR pass, then the blitter places the object over
the live stars. The 4,032-byte colour/mask cache fits the existing 5,120-byte buffer.
Blue steel, cyan and white foreground colours remain independent of the galaxy.

The galaxy compresses from 20,480 to 5,381 bytes and decodes once into OLD on
scene entry. DMA reads the two background planes directly from that cache.
Deep Space uses a direct entrance because OLD is occupied by the background.
Removing the duplicate half of the periodic scroller wave table saves another
1,024 bytes without changing its sine heights. Together these changes allow the
new 15,216-byte reactor bank while reducing CHIP allocation from 482,304 to
481,792 bytes. All assets remain within the project's 472 KiB allocation guard.

The artifact checks cover all reactor poses, padding words, generated masks,
scratch-buffer bounds and stage bounds. `validation/space-reactor-native-check.py`
compares the actual emulator cache and background DMA pointers with the immutable
launched build. Physical OCS testing is still outstanding.
For binary `c3fd8353009f871849a42b7ade27d9dd2f24afd4cb4b2702e0c386ab1985d7f1`,
the [native check](../validation/space-reactor-native.json) matched the complete
20,480-byte background, 4,032-byte reactor cache and both background DMA pointers.
The scene measured 43.40 FPS over 371 VBLs, compared with 49.77 FPS in the
[previous scene](../validation/space-reactor-baseline.json) without the reactor.
These are cycle-exact emulator measurements with startup frames excluded.

## Independent roto background motion, 23 September 2026

`tools/roto_background.py` prepares seventeen 320×176 masks at 2° intervals.
The background traverses them in both directions, taking 5.12 seconds for a full
rocking cycle; the foreground continues its continuous spin. A small blur before
thresholding reduces flickering speckles. All source and destination rows stay
inside the scene area, leaving header and HUD rows clear.

Two full planes borrowed from OLD alternate as background buffers after the
entry transition. DMA reads the completed plane while the other is decoded.
The first LZSS implementation measured 24.22 FPS versus the static background's
36.40 FPS. A dedicated word-run decoder replaces the byte-token path, filling long
blank spans eight words at a time. The native checker validates the cache bytes,
distinct buffer addresses and the complete pose selected by actual display DMA.
The foreground decoder also loads its byte count as a full longword, so a caller's
CHIP pointer cannot leave stale upper bits in the requested output length.

To fit the new bank, the runner's sunset is stored as two compressed streams.
Its first two planes decode once into OLD, and its third into MASKBUF; the three
DMA pointers work in both shaded and dot modes. All 30,720 decoded bytes were
compared with the preceding release and are identical. The runner now enters
directly, since those buffers are occupied by its background. Scene entry resets
the cache flags before any borrowed buffer is reused.

For binary `19996cc3ed46884f975aaf2c8383ed036d09e3dbe98aa0c814d3aa25fae89430`,
the [uninterrupted timing sample](../validation/roto-motion-final.json) measured
31.18 FPS over 473 VBLs, with both layers moving, versus 36.40 FPS for the static
backdrop. It uses counter deltas to exclude the earlier paused inspection.
The [native checks](../validation/roto-motion-native.json) verified the complete
10,240-byte displayed background, 3,200-byte checker pose and both runner modes'
30,720-byte sunset cache. The final CHIP allocation is 481,792 bytes, unchanged
from the preceding build and within the 472 KiB guard. Physical OCS testing remains.

## Opposite roto directions, 23 September 2026

The galaxy now makes complete counterclockwise turns, opposite the clockwise
checker plane. Both complete a turn in 256 PAL ticks (5.12 seconds). Sixteen
320×176 masks cover the first half-turn; the second half decodes backwards with
reversed bits directly into the unpublished buffer. It then swaps into display
DMA. This avoids a separate image pass and needs no extra scratch allocation.

The packed background bank is 23,006 bytes. CHIP allocation falls by 4,096 bytes
to 477,696. Artifact tests compare all 32 reconstructed angles with direct image
rotation, including the half-turn and wrap boundaries. Header and footer rows
remain blank in both background buffers.

For binary `ba56ac5f3d5ce7c026970ad8732ad4d1f1a7feeed6c5464d0f0d2830fd4d9cfd`,
native checks verified the full background and foreground caches at angles 10
and 27, covering both decoder directions. The [unpaused timing sample](../validation/roto-opposite-final.json)
measured 295 presentations over 473 VBLs (31.18 FPS), with music enabled. The
initial separate-flip version measured 25.90 FPS; direct reverse decoding
restores the previous rocking version's measured cadence.

## Solid-shape variety, 23 September 2026

The centre cube uses a 64-pixel canvas, with 32-pixel boxes, tetrahedra and
triangular prisms plus 40-pixel octahedra around it. Each family has sixteen
perspective-projected poses, with different spin phases, alternating rotation
directions and a changing tilt. Six satellites follow a wider ellipse while
the central cube bobs. Copper colours change across height and time, giving
faces travelling coloured reflections over the starfield.

Five compressed banks unpack once at scene entry. Their 49,152 bytes borrow
OLD, MASKBUF, the hires area and the roto pair. Animation copies the selected
poses into the 4,608-byte GRAPHBUF cache and generates silhouettes there.
The scene enters directly because OLD holds poses instead of the transition
image. Scene initialization invalidates the shared cache on each entry.

The briefing is also stored compressed and decodes into HIWORK, preserving
its existing reveal. The resulting CHIP allocation is 478,720 bytes, below
the 472 KiB guard. Tests cover all poses, padding words, cache capacities,
colour variety and satellite blit bounds throughout the scene.

Binary `19003a63df7a6da6a5a39f70c49ac46d51b0616e0a2c2af9fb081f8c289a17d5`
measured 37.39 FPS (353 presentations over 472 VBLs) in an
[unpaused complete-scene sample](../validation/solid-shapes-final.json).
The simpler preceding scene measured 49.89 FPS. Preloading replaces the first
implementation's per-pose decompression, which measured 23.86 FPS in a short
44-VBL sample. [Native checks](../validation/solid-shapes-native.json) compared
all 49,152 bank bytes and the 4,608-byte drawing cache, verified 40 distinct
colour bands, and checked the briefing after cache reuse. The big scroller was
also inspected before returning to and revalidating Solid Cubes.

## Slower train and grounded fighters, 23 September 2026

The artwork carriage and both fighter roots now use one displacement function:
`FRAME >> 2`, giving 12.5 source pixels per second at PAL timing. The fighters
retain fixed horizontal offsets on the carriage while their attack animations
continue. Both stay inside the viewport throughout the 512-tick scene.

The roof line now coincides with the carriage's top at y144. Each fighter pose
has a ground line derived from its last opaque pixel row; sprite publication
places that row directly above the roof. Carriage, roof and fighters share the
same vibration, now changing every four ticks. Roof markings also scroll with
the carriage. The R comparison retains the original horizontal choreography.

[Native snapshot checks](../validation/train-anchor-native.json) compare the
actual scrolled carriage pixels, roof row and all six sprite DMA headers.
Multiple animation frames preserve carriage-relative x offsets of 176 and 246
pixels, with each fighter's lowest opaque pixel immediately above the roof.
All 103 pose ground lines are also checked against their bitmap data.

## Verification and remaining refinement

`make test` checks disk checksum/payload, pinned sources, body bounds, sprite DMA,
pose pacing, hires shifts/stretching, rotating glyphs, parallax wrap and occlusion.
`python3 validation/tunnel-geometry-check.py` checks all generated tunnel phases for
closed parity, write bounds and nearest-wall viewport coverage.

The packaged binary is identified in [build-info.json](../dist/build-info.json).
The earlier 13 September preview's SHA-256 was
`5e82bfa5d2bcf8c205b9f38038611f25707ede4c729ddca4409f0081566db921`.
FS-UAE checks confirmed the raised city, faster matched fighters and spinning
text. The [native font check](../validation/september-refinement-big-spin.json)
matched all 19,920 cached bytes, including the wrap seam. The
[fighter preview](../validation/september-refinement-fighter-tempo.json) measured
about 24 FPS. Big text measured about 19 FPS in the preceding build with the
same renderer. These are cycle-exact emulator samples, not physical-hardware
measurements or a clean uninterrupted playlist benchmark.

Outstanding work:

- Investigate FS-UAE mouse/focus interactions that can leave playback muted;
  M was verified to enable audio and the HUD bars during this pass.

- Continue profiling the large scroller beyond the current 20 FPS and compare
  shaded and dot runner costs.
- Test on physical OCS hardware.
- Improve transitions where extra background colours cannot be represented by
  the frozen two-plane image. New train art and big text enter directly.
- Consider larger foreground silhouettes after physical-hardware validation;
  fast tumbling leaves now provide a third moving depth layer.
- Refine airborne and sweep choreography; selected modern poses do not match
  every Spectrum move exactly, and the source packs contain unused moves.

Earlier measurements and implementation decisions are retained in
[the refinement history](refinement-history.md). Each validation JSON identifies
its own binary; older results do not describe the latest build.


## Robotsound MOD soundtrack, 23 September 2026

The user-selected **"robotsound" by k0wax** replaces the procedural four-theme
arrangement. The original four-channel MOD is retained unchanged, with its CC0
source link and embedded Basehead sample attribution in
[music provenance](../assets/music/SOURCE.md). The native replay code is the
MIT-licensed standard Light Speed Player v1.31, pinned and credited under
[vendor/lsplayer](../vendor/lsplayer/README.md).

The converter prepares a fixed 50 Hz event stream. The track's speed changes
are preserved; its complete pass is 8,837 ticks, approximately 176.74 seconds.
The score loops independently of the scene clock. Direct scene selection,
automatic transitions, mute and scene pause never reinitialise it. The four shadow volume registers feed Paula. Mute writes zero to Paula while
the underlying music events continue. The HUD uses separate sample-peak
envelopes rather than the persistent volume settings.

The 19,754-byte score and 17,674-byte meter table occupy a 37,888-byte
allocation in the A500's slow RAM. The 13,994-byte sample bank stays in CHIP RAM. The boot loader reads the score
from the sectors following the aligned graphics/code payload. CHIP allocation is
482,304 bytes, below the unchanged 483,328-byte project ceiling. Target hardware
remains 512 KiB CHIP plus 512 KiB slow RAM, with no fast-memory expansion.

`make test` decodes two complete loops, checks channel activity, stream rewind,
DMA ranges, boot checksum, separate score placement and pinned source hashes.
The source-conversion script reproduced the checked-in score and sample bank
byte for byte. The WAV preview is generated from those same converted events.

[Native emulator observations](../validation/robotsound-native.json) were checked
using `validation/music-native-check.py` against the immutable launched build.
Actual Paula periods, volumes, sample pointers and lengths matched the decoded
score, as did the native replay stream pointers. Observations include selecting
Night Train mid-song, playback after the loop boundary, mute, unmute while scene
animation remained paused, and resuming animation. Music ticks remained equal to
total VBL ticks throughout. These are cycle-exact FS-UAE checks, not real-hardware
measurements.


### HUD meter correction

The initial MOD integration displayed Paula volume settings. These can stay
nonzero after a one-shot sample reaches silence, so the bars appeared stuck.
`tools/music.py` now derives per-channel peaks while rendering the same sample
stream used for the preview. A square-root response keeps quieter parts visible;
falloff is two of fifteen level steps per PAL tick, up to 160 ms from a full peak.
The packed table lives beside the score in slow RAM. A small VBL update selects
the current levels and clears them when muted. The waveform and MOD replay are
unchanged, and the CHIP allocation remains 482,304 bytes.

The regression checks cover a loud one-shot fading to zero at constant volume,
a silent sample with a nonzero volume setting, and quieter versus louder looping
samples. Every real soundtrack channel must change height while its volume
setting remains constant and must have silent tails whose meters reach zero.

Native FS-UAE checks also verified the new level words against the packed meter
table, observed a zero meter with a nonzero channel volume, and checked all four
visible bar pixel columns were clear while muted. Observations remain in
`validation/robotsound-native.json`, distinguished by the loaded binary hash.
