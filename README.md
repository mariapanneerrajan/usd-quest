# Pixel Forge

A gamified OpenUSD mastery desktop game — walks complete novices in the VFX and animation industry through every concept OpenUSD offers, from stages and prims all the way up to custom schemas, Hydra render delegates, and asset resolvers. The player is a new TD at a fictional studio; each Act is a production scenario graded by the USD API itself.

Licensed under the [MIT License](LICENSE).

## M0 — Foundation

Embeds Pixar's `Usdviewq.StageView` (Hydra Storm) in a PySide6 window and loads `Kitchen_set.usd`.

### Prereqs

- A local OpenUSD build at `C:\code\open_usd\USDinst` (built against `C:\Python310\python.exe`). Override with `PIXELFORGE_USD_ROOT`.
- `uv` on PATH.

### Run

```bash
uv sync
uv run pixelforge
```

Optional: pass a stage path as the first arg.
