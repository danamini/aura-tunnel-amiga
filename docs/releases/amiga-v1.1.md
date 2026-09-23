Aura Tunnel Amiga is a ten-scene demo built with AI for the Amiga 500. I had a ZX Spectrum and an Amiga as a child, and these demos use AI to help me realise ideas I couldn't build on those machines on my own.

This release adds:

- A twelve-sided twisting tunnel with illuminated rails and moving neon colours.
- A galaxy background rotating opposite the checker plane in Copper Roto.
- Higher-resolution spinning scroll letters and animated colour reflections.
- A larger central cube with orbiting boxes, diamonds, tetrahedra and prisms.
- An orbital reactor at the centre of Deep Space.
- Four-channel music with changing themes, instruments and fills, plus HUD level meters.
- A slower train with fighters anchored to its roof, shared bounce and fast passing leaves.
- A README screenshot gallery and updated build and validation notes.

Rendering uses cached poses, compressed artwork and shared scene buffers. The disk targets PAL Amiga 500 / OCS, a normal-speed 68000, 512 KiB CHIP and 512 KiB slow RAM. The full scene sequence lasts 128 seconds.

Download `aura-tunnel-amiga.adf` and open it in FS-UAE with those settings. Keys 1–9 and 0 select scenes; M toggles music; Space pauses scene time. `music-preview.wav` is rendered from the score. `NOTICE.txt` contains the credits and licences, and `build-info.json` identifies the disk and binary by SHA-256.

Validated with artifact checks, tunnel geometry checks and FS-UAE scene inspections. Physical OCS hardware testing remains outstanding; detailed measurements and further work are in `docs/implementation-plan.md`.
