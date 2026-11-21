---
name: pixel-composer
description: Answer questions about Pixel Composer (pixel-composer.com), a node-based VFX compositor for pixel art. Use whenever the user asks about PXC nodes, panels, particle systems, 3D rendering, shaders, Lua scripting, GameMaker/Aseprite/Krita I/O, or any feature in docs.pixel-composer.com. Also covers automating PXC — the headless command line, console commands, the Argument/Shell/File/Network nodes, the .pxc file format, and running it under Proton on Linux. Trigger on: "pixel composer", "PXC", mentions of specific node names (e.g. "the noise node"), or questions about how to build a VFX graph.
---

# Pixel Composer Assistant

Pixel Composer (PXC) is a node-based VFX compositor for pixel art by MakhamDev. Users build effects by connecting 300+ nodes in a visual programming graph: patterns, fluid sims, particles, 3D, shaders, animation curves, exports to sprite sheets / GameMaker / Aseprite.

## How to answer PXC questions

1. **Fetch fresh — don't answer from memory.** PXC ships new nodes often; training data rots. Always WebFetch the relevant doc page before answering.
2. **Cite the URL** you pulled from so the user can verify and dig deeper.
3. **Prefer the specific node page over the category index.** URLs are predictable: `https://docs.pixel-composer.com/nodes/<category>/<node_name>.html`. If you don't know the exact node name, fetch the category index first.
4. **For conceptual questions** (workflow, "what's the best way to…"), supplement docs with the forum or YouTube — the reference describes *what* nodes do, not always *why* or *when*.
5. **Batch WebFetches** in parallel when multiple pages are relevant.

## Documentation map

**Root:** https://docs.pixel-composer.com

### Top-level
- **Getting Started:** https://docs.pixel-composer.com/getting_started.html
- **Interfaces:** https://docs.pixel-composer.com/interfaces/index.html
  - Panels: Animation, Collection, Color Selector, Graph, Inspector, Nodes, Preview (2D), Preview 3D, Tunnels
- **Nodes index:** https://docs.pixel-composer.com/nodes/index.html

### Node categories (all under `/nodes/<category>/`)
| Category | Covers |
|---|---|
| **IO** | Image import/export, Aseprite, Krita, Ora, Pxc, GameMaker, Tileset, Canvas, File, External, Device, Network |
| **Transform** | Crop, warp, scale, align, flip, mirror, offset, background |
| **Filter** | Blur, color adjust, effects, warping, convolution, analysis |
| **3D** | Scenes, materials, meshes, lights, ray marching, point ops |
| **Generate** | Color, drawer, noise, pattern, population, simulation, region, UV, effects |
| **Compose** | Armature, blending, compositing, sprite packing |
| **Values** | Structs, mesh, atlas, buffers, numbers, vectors, matrices, text, arrays, paths, boolean |
| **Animation** | Curves, audio, loops, delays, rate remapping |
| **Particle** | 2D/3D particle systems, VFX, affectors |
| **Utility** | Control flow, groups, Lua, shaders, caching, debug, project, system |

### Specialized workflow pages
- **Pixel Builder:** https://docs.pixel-composer.com/nodes/pixel_builder/index.html
- **Mk Tree:** https://docs.pixel-composer.com/nodes/mk_tree/index.html
- **Iteration:** https://docs.pixel-composer.com/nodes/iteration/index.html
- **Particle Systems:** https://docs.pixel-composer.com/nodes/particle/index.html
- **Pcx programming:** https://docs.pixel-composer.com/nodes/pcx/index.html

## Automation and agent interfaces

PXC is GUI-first but it is not GUI-only. Verified against an installed 1.21.8 build
on 2026-10-21; cite the two docs pages below rather than this summary when answering.

### Headless CLI

```
./PixelComposer.exe <path to project.pxc> [tags] [global variables]
```

| Tag | Effect |
|---|---|
| `-h`, `--headless` | Run without the UI. All nodes run once, then **export nodes trigger automatically** |
| `-t`, `--trusted` | Allow Execute Shell nodes, which are disabled by default in headless mode |
| `-sl`, `--skiplua` | Skip Lua initialization |
| `-name value` | After the tags, sets a **global variable** — the hook that pairs with the `Argument` node (Misc > System) |

**It cannot write to stdout** (a GameMaker limitation, stated in the docs), so a
headless run gives no textual feedback. A separate **CLI wrapper** `.exe` must be
downloaded to get `-v/--verbose`, `-p/--persist` and `-s/--server [port]`.

With `-p` the project runs once and an interactive shell opens that takes **console
commands**, not CLI arguments: `set [name] [value]`, `render`, `flag [debugFlag]`,
`exit`. That makes parameter sweeps possible in one process. `--server [port]`
exposes the same over TCP but upstream marks it "not tested yet."

- Command line: https://github.com/Ttanasart-pt/Pixel-Composer/blob/main/docsdata/content/99_misc/command_line.html
- Console commands: https://github.com/Ttanasart-pt/Pixel-Composer/blob/main/docsdata/content/99_misc/console_command.html
- Flag parsing: `objects/o_main/Create_0.gml`; introduced in `releases/1.16.6.md`

### Nodes that reach outside the graph

- **Misc > Lua** — `Lua Compute`, `Lua Global`, `Lua Surface`
- **Misc > System** — `Argument` (receives CLI globals), `Shell` (runs shell commands; confirmation popup unless `--trusted`), `Application In`/`Out`, `Terminal Trigger`, `Monitor Capture`, `Assert`
- **Misc > Shader** — `Hlsl`
- **IO > File** — `Json`/`Csv`/`Xml`/`Text`/`Byte`/`Wav File Read`+`Write`, `Directory Search`
- **IO > External > Network** — `Http Request`, `Http Request File`, `Websocket Sender`/`Receiver`

So a graph can read a JSON file an agent wrote, or call an endpoint an agent serves.

### The .pxc format

Undocumented, but readable. Layout as written by 1.21.8:

```
0x00  "PXCX"   magic
0x04  u32      absolute offset of the project payload
0x08  "THMB"   thumbnail chunk tag
0x0c  u32      compressed length of the thumbnail
0x10  zlib     thumbnail, inflating to raw RGBA (256*256*4 = 262144 bytes)
...   zlib     the project: UTF-8 JSON, NUL-terminated
```

The project JSON holds `versions`, `version` (format number), `metadata`, `nodes`
(each with `type` such as `Node_Export`, `name`, `id`, `x`/`y`, `inputs`, `outputs`),
`global_node`, and panel/layout state. A node input is a dict whose current value
sits at `r.d`, with `from_node` naming its upstream connection — e.g. an
`Node_Export` keeps its output directory in `inputs[1].r.d` and its filename
template (`%d%n`) in `inputs[2]`.

Read one with `tools/pxc/pxc_read.py` in this repo: summary by default,
`--json OUT` to dump, `--node ID` for a single node. It parses both the 120000 and
121070 format versions. Being undocumented, the layout can shift between PXC
releases, so treat it as inspect-and-tweak, never author-from-scratch.

### Running it on Linux

There is a **native Linux build** (since 1.21.8). Steam ships it as depot `2299513`:
a single `PixelComposer.AppImage`. If the install directory holds `PixelComposer.exe`
and ~49 DLLs instead, a compatibility tool is forced for the app — clear Properties →
Compatibility in Steam and it swaps depots. Prefer the native build: the Windows
runner under Proton has no stdout, which makes every failure look identical.

Steam's `launch.sh` runs `PixelComposer.AppImage --appimage-extract-and-run "$@"`.
For repeated runs, extract once and drive the inner `AppRun`:

```bash
APPDIR="$HOME/.local/share/Steam/steamapps/common/Pixel Composer"
"$APPDIR/PixelComposer.AppImage" --appimage-extract          # -> ./squashfs-root
SteamAppId=2299510 ./squashfs-root/AppRun /abs/path/project.pxc --headless
```

**`SteamAppId` is mandatory.** Without it the Steamworks extension aborts before the
app starts: `RestartAppIfNecessary check failed, the game is not allowed to continue`.
A `steam_appid.txt` file does *not* substitute — the build reports
`steam_appid.txt file not found` wherever it is placed. Steam must also be running.

The native runner prints everything to stdout (`YoYo Games Linux Runner V1.3`),
including PXC's own argument echo and CLI banner — so arguments are provably received:

```
    >>> params 0: /abs/path/project.pxc
    >>> params 1: --headless
CLI: Running PixelComposer 1.22.0.5
```

Config and saves move to `~/.config/PixelComposer/`, so projects and recent-file
lists left behind in a Proton prefix are not picked up. Lua works — `Apollo.so` ships
in `usr/bin/assets/`. Bundled helpers (`imagemagick`, `gifski`, `webp`) carry `linux/`
variants; ffmpeg is fetched on demand for license reasons.

Harmless startup noise: `dlopen` failures for `*_linux_arm64-v8a.so` (Box2D, brotli,
bz2, freetype, libpng16). The extension definitions carry arm64 library names; the app
continues past them.

**Headless is broken on 1.22.0.5 (verified 2026-10-21, native Linux build).** Any
project path plus `--headless` (or `-h`) crashes immediately after init:

```
Unable to get variable lock_panel from object ...
gml_Script_Panel_Menu (line 271)
gml_Script_panelObjectInit (line 73)
gml_Script_refreshPanel (line 103)
gml_Script_display_refresh (line 14)
```

Reproduced with a 32-node vendor sample and a 5-node project, with both `-h` and
`--headless`, and with `--persist` / `--render` / `--trusted` / `--skiplua` — identical
every time. The same invocation **without** a project path reaches the CLI cleanly
(`Cmd mode with empty path. exiting...`), and the **GUI launches and runs fine**, so
only the headless project-open path is affected.

Root cause, traced in the source: `scripts/preferences/preferences.gml:681` sets
`CLICK_REFRESH = true` **on Linux only**; `objects/o_main/Step_1.gml:104` acts on it
without checking `IS_CMD`, calling `display_refresh()` -> `refreshPanel()` ->
`Panel_Menu()`, which reads `MENU_ITEMS.lock_panel`. `MENU_ITEMS` is only populated by
`__fnInit()`, skipped in CLI mode at `objects/o_main/Other_2.gml:184`, so it is empty.
Same family as upstream
[#114](https://github.com/Ttanasart-pt/Pixel-Composer/issues/114) (`PANEL_ANIMATION`
undefined in CLI mode) and
[#117](https://github.com/Ttanasart-pt/Pixel-Composer/issues/117): UI state reached
while `IS_CMD` is set.

Because the trigger is guarded by `OS == os_linux`, this is **not** what stopped the
earlier Proton run of the Windows build. That failure — silent exit 0 right after
`Initialization complete` — remains unexplained, and the Windows runner has no stdout
to diagnose it with. Use the native build for any further headless work.

**So do not build automation on the headless CLI yet.** Reading `.pxc` files
(`tools/pxc/pxc_read.py`) and the in-graph nodes are the surfaces that actually work.

## Community resources

- **Forum:** https://forum.pixel-composer.com/
- **Discord:** https://discord.gg/aHGbYjQh63
- **YouTube (MakhamDev):** https://www.youtube.com/@makhamdev
- **GitHub (source, issues):** https://github.com/Ttanasart-pt/Pixel-Composer
- **Patreon:** https://www.patreon.com/MakhamDev

## Answering workflow

1. Parse the user's question — identify node name, category, or concept.
2. Pick the most specific URL from the map. If unknown, fetch the category index.
3. WebFetch the page(s). Batch in parallel if multiple.
4. Answer concisely, cite the URL(s).
5. If docs are thin on the topic, point to the forum or a YouTube search as a follow-up.

## Notes on the app itself

- Developer: MakhamDev (Ttanasart-pt on GitHub), first released 2023.
- Targets pixel artists doing VFX — explosions, auras, particles, animated sprites, tilesets.
- Outputs can feed directly into **GameMaker** projects (dedicated IO nodes) and standard image formats.
- Supports **Lua scripting**, custom **shaders**, and **feedback loops** for simulations.
