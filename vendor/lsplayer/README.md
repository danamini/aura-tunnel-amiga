# Light Speed Player

Native MOD replay by **Arnaud Carré / Leonard / Oxygene**,
[upstream repository](https://github.com/arnaud-carre/LSPlayer),
revision `fa9c93cd304ead7076e0fce8a1c89d9286d81f9c`, under the [MIT licence](LICENSE).

`LightSpeedPlayer.asm` is the standard v1.31 player from that revision. Local
changes convert the source text to UTF-8 and direct its four volume writes into
`LSPVolumes`. Our wrapper writes those values to Paula, or zero when muted. Separate
sample-peak envelopes drive the HUD meters. This preserves the track's volume changes while muted. The score keeps
advancing during mute and scene pause. The Copper restarts retriggered audio DMA
at line 32, after the player's VBL register writes.

The external build-time converter uses Martin Cameron's micromod and the
Shrinkler components credited in its source. Converter binaries and those
libraries are not distributed in this repository or the demo. The native replay
source and its MIT notice are included here and in the release notices.

See [music provenance and reproduction](../../assets/music/SOURCE.md).
