# Credits and source terms

Aura Tunnel Amiga is by Daniel Amini, built with AI assistance for research,
code, artwork preparation and hardware experiments. Daniel chose the scenes,
reviewed the demos and shaped their appearance and sound. The project also uses
the artwork, motion data and melodies credited below.

The project's original code and arrangements are covered by the [MIT licence](LICENSE).
Third-party assets retain their own terms; MIT does not replace those terms.
The [release notices](dist/NOTICE.txt) collect these credits and the retained
licence and provenance texts. Please keep those notices with redistributed copies.

## Spectrum source

This is a companion to [Aura Tunnel for ZX Spectrum](https://github.com/danamini/aura-tunnel),
also by Daniel Amini. The [pinned reference files](assets/reference/),
[SHA-256 manifest](assets/reference/manifest.json) and
[original licence](assets/reference/LICENSE) record the material used for the port.

That retained licence also documents the Spectrum project's Konami-derived
Yie Ar Kung-Fu reference. No Konami artwork is included in the native Amiga
payload, and the Konami sprite binary is excluded from this repository.
The fighters used here are the separately sourced CC0 artwork below.

## Fighters

Mustermann 2 and Jones from Bad Company are by **Puffolotti Accident**,
listed as Puffolotti on OpenGameArt, and released under
[CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/).
See also the [full CC0 legal text](https://creativecommons.org/publicdomain/zero/1.0/legalcode.en).

- [Mustermann 2 source page](https://opengameart.org/node/97941) and [original GIF](https://opengameart.org/sites/default/files/1_8.gif).
- [Jones / Bad Company source page](https://opengameart.org/content/bad-company-assorted-military-thugs-universal-prototype-2-for-scrolling-beat-em-up-or-mugen) and [original GIF](https://opengameart.org/sites/default/files/jones_selection_01_karatecretin_sequence.gif).
- [Local originals, file hashes and conversion details](assets/fighters/SOURCE.md).

The build selects 56 Mustermann poses and 47 Jones poses, crops fixed canvases
and converts them to three opaque colours per character. Compressed poses become
48×56 hardware sprites; mirroring supplies the opponent's facing direction.
R retains a comparison using the earlier 47-pose Mustermann pair. The complete
original packs are archived separately, outside this demo's disk payload.

## Night Train scenery

The sourced scenery uses two works released under
[CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/):

- [Parallax City Night (4 Colors)](https://opengameart.org/content/parallax-city-night-4-colors)
  by [FisherG](https://opengameart.org/users/fisherg). The source also credits
  **PixelCod** for the **Ghost (Vibrant)** palette. Retained layers:
  [sCityFar.png](assets/art/sCityFar.png), [sCityMid.png](assets/art/sCityMid.png)
  and [sCityClose.png](assets/art/sCityClose.png).
- [Pixel Train Scene](https://opengameart.org/content/pixel-train-scene)
  by **mrti14**. Retained original: [pixel-train.png](assets/art/pixel-train.png).

The build composites the city layers, scales the train and converts both to
two-plane parallax artwork with an Amiga palette. R switches to the project's
procedural backdrop. The downloaded PNGs are retained for provenance.

## Motion capture

The runner uses subject 09, clip 01 from the
[CMU Graphics Lab Motion Capture Database](https://mocap.cs.cmu.edu/),
converted to BVH by **Bruce Hahne**. The conversion is available from the
[CMU BVH mirror](https://github.com/una-dinosauria/cmu-mocap/blob/master/data/009/09_01.bvh).
The demo derives projected poses from this motion data.

The data used in this project was obtained from mocap.cs.cmu.edu.
The database was created with funding from NSF EIA-0196217.

The retained [provenance](assets/reference/assets/mocap/SOURCE.md) and
[original conversion documentation and usage rights](assets/reference/assets/mocap/READMEFIRST.txt)
record the source and reuse terms.

## Music

The current soundtrack is **"robotsound" by [k0wax](https://modarchive.org/member.php?82798)**,
from [The Mod Archive, module 168066](https://modarchive.org/index.php?request=view_by_moduleid&query=168066),
listed under the **[CC0 1.0 Universal public-domain dedication](https://creativecommons.org/publicdomain/zero/1.0/)**
([full legal text](https://creativecommons.org/publicdomain/zero/1.0/legalcode.en)).
The soundtrack retains those terms; the project's MIT licence covers its original
code and arrangements. The replay engine has its own MIT notice below.

The module's embedded notes also credit **Basehead** for samples and identify
samples 3 and 9 as the author's own. Those notes remain in the original file.

The untouched [original MOD](assets/music/k0w-rsnd.mod),
[conversion details](assets/music/SOURCE.md) and
[file hashes](assets/music/manifest.json) are included in the repository. The track plays in a continuous loop through scene
changes. We did not compose this soundtrack or create its samples.

Playback uses **Light Speed Player** by **Arnaud Carré / Leonard / Oxygene**,
under its own [MIT licence](vendor/lsplayer/LICENSE).
The [upstream source](https://github.com/arnaud-carre/LSPlayer) and
[local modifications](vendor/lsplayer/README.md) are documented. Its external
converter also uses Martin Cameron's micromod and the Shrinkler components
credited upstream. The native replay code and its licence are included here.

The [downloadable WAV](dist/music-preview.wav) is a software render of the
converted replay events and samples, not a hardware recording.

Earlier Amiga versions used the Spectrum show's Korobeiniki, Neon Drive,
Beethoven's Ode to Joy and Night Flight. Their score remains in the
[pinned Spectrum reference](assets/reference/tools/gen_ay128.py). The traditional
Korobeiniki and Beethoven melodies are public domain; the project's original
themes and arrangements retain their MIT terms. Those themes are no longer the
Amiga demo's soundtrack.

## Fonts and generated graphics

The small HUD alphabet is original code in [tools/hud_font.py](tools/hud_font.py).
Large outlined lettering comes from the pinned Spectrum project's
[vector strokes](assets/reference/tools/gen_font.py), covered by its MIT licence,
with the Amiga conversion in [tools/hires_font.py](tools/hires_font.py).

Sunset, galaxy, planet, terrain and the original train strips are generated by
this repository. The sourced fighter and scenery artwork is credited above.

## Development tools and research

- [vasm](http://sun.hasenbraten.de/vasm/) assembles the 68000 code. The
  [bootstrap script](tools/bootstrap.sh) pins a revision of the
  [vasm source mirror](https://github.com/StarWolf3000/vasm-mirror).
- [Pillow](https://python-pillow.org/) processes images during the build.
- [FS-UAE](https://fs-uae.net/) runs the demo and captures screenshots, using its
  internal [AROS](https://aros.sourceforge.io/) replacement ROM.

These are external development tools. Their binaries and ROMs are not committed
or included in the demo release. Their own terms apply to those tools.
The [implementation notes](docs/implementation-plan.md) link the hardware manuals,
community examples and research used during development, and record the graphics implementation choices. The imported music replay
code is credited separately above.
