# Aura Tunnel Amiga

An Amiga 500 / OCS companion to [Aura Tunnel for ZX Spectrum](https://github.com/danamini/aura-tunnel), preserving its ten-scene sequence and
music while adding Amiga colour, sprites, blitter effects and chrome lettering.

I started this, like the Spectrum version, to see how AI could help me make
things I wanted to make. I set the direction, watched the demos run and kept
asking for changes; AI helped with the research, code, asset preparation and
hardware experiments. The Amiga version keeps the same scenes so I can compare
what the two machines can do, and see how far that collaboration can take it.
It is also a learning exercise: the same effects expose different trade-offs on
the Spectrum and Amiga, from Z80 and 68000 code to colour, memory, sprites,
Copper, blitter and sound. Keeping the scene structure makes those differences
easier to see and understand.

**Development preview, 13 September 2026.** The visual pass is unfinished.
[Download the bootable ADF](dist/aura-tunnel-amiga.adf) with its [notices](dist/NOTICE.txt), or build from source.
Known display and performance issues are recorded in the [implementation plan](docs/implementation-plan.md#verification-and-remaining-refinement).

Run `make setup` to create a Python environment, install the pinned Pillow version
and build a pinned vasm revision. Then run `make test` and `make emu`. The macOS launcher defaults
to `/Applications/FS-UAE.app/Contents/MacOS/fs-uae`; set `FS_UAE` for another path.
FS-UAE's internal AROS replacement ROM boots the disk without a proprietary ROM.

The output is `build/aura-tunnel-amiga.adf`. Target settings are PAL A500, OCS,
normal-speed cycle-exact 68000, 512 KiB CHIP, 512 KiB slow, no fast RAM.

## Controls

- Left mouse: next scene. Right mouse: music on/off. Music starts on; the HUD shows its state.
- R: bodies/dots in Dot Runner; new/original art in Night Train. Each scene shows a prompt.
- 1 through 9, then 0: select the ten scenes directly.
- Space: pause/resume scene time for inspection. Audio timing continues.
- F5/F6: save emulator states 1/2. F7: save a screenshot. F12: emulator menu.

The runner scene lasts 15.36 seconds, with slow and fast companions and a
bright on-screen R prompt. The graph scene now runs the complete calculation
without artificial pacing and shows a measured implementation comparison:
Spectrum ROM BASIC versus native 68000 fixed-point arithmetic. It is not a
BASIC-to-BASIC or CPU-only benchmark. See [measurement details](docs/graph-comparison.md).

Read `docs/implementation-plan.md` for adopted research, validation and remaining
refinements. `tools/read_snapshot.py --save` reads counters from the running
immutable build, not from symbols belonging to a later rebuild.

The repository naming convention is `aura-tunnel-<platform>` for companion ports.
`aura-tunnel` remains the original Spectrum repository; this port is
[`aura-tunnel-amiga`](https://github.com/danamini/aura-tunnel-amiga).

This repository is separate from the Spectrum source. Its pinned references and
hashes are in `assets/reference`. See `CREDITS.md` for artwork, motion and music.

Night Train's new mode pairs Mustermann with Jones and uses credited CC0
city/train strips. The central chrome scroller uses 640 horizontal pixels with
Copper-repeated rows, a larger sine range and moving chrome reflections.
The AI and ZX letters periodically spin through 16 poses; upright letters keep
the full horizontal detail, while rotating poses use a compact mask expanded
by the 68000. The smaller scroller also rolls individual letters at a slower
pace so the comparison message stays readable.
