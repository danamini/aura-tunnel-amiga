# Robotsound soundtrack

- Title: **"robotsound"**.
- Artist: [k0wax](https://modarchive.org/member.php?82798).
- Original: [k0w-rsnd.mod](k0w-rsnd.mod), 27,362 bytes, four-channel ProTracker MOD.
- Source: [The Mod Archive, module 168066](https://modarchive.org/index.php?request=view_by_moduleid&query=168066).
- Published terms: **CC0 1.0 Universal public-domain dedication**.
  [Summary](https://creativecommons.org/publicdomain/zero/1.0/),
  [legal text](https://creativecommons.org/publicdomain/zero/1.0/legalcode.en).
  The source page was checked on 23 September 2026.

The module's embedded instrument names credit **Basehead** for samples and say
"3,9 - my own". Those notes remain in the untouched original MOD. We retain that
sample attribution alongside k0wax's track credit; we did not create this music.

The Amiga demo plays the track continuously and loops it. Selecting a scene,
pausing scene animation or muting does not restart or replace the soundtrack.
One converted pass is 8,837 PAL ticks, approximately 176.74 seconds.

## Conversion

[Light Speed Player](../../vendor/lsplayer/README.md) converts the MOD into
`robotsound.lsmusic` and `robotsound.lsbank`. The score and precomputed meter envelopes use slow RAM; the 13,994-byte
sample bank uses CHIP RAM. The original file is preserved byte for byte.

For conversion only, zero sample-repeat lengths are normalised to one word,
the conventional silent two-byte loop. Musical patterns are unchanged. The converter also clears silent
sample-loop bytes as part of its normal ProTracker sample preparation.

Run `python3 tools/convert_music.py /path/to/LSPlayer` to reproduce the files.
The tool requires the pinned upstream revision and a C++17 compiler. It builds
the converter locally, without installing it, and applies a macOS/Linux
`strncpy_s` compatibility alias. The upstream CMake version is stale, so the
build explicitly selects v1.31 to match the pinned player and converter source.

[manifest.json](manifest.json) records SHA-256 values of the original MOD,
converted data, and included replay source and licence. Normal builds use those
checked-in files. `tools/music.py` independently decodes the replay events to
produce the downloadable stereo WAV preview; that preview is a software render,
not an Amiga hardware recording.

The four HUD meters use per-channel sample peaks from the same software render,
with a square-root response and short decay. The packed envelopes follow the
MOD clock, so silent sample tails fall to zero even when Paula volume stays set.
Muting clears all four displayed levels.
