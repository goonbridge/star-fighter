# Star Fighter (3DO) -> cross-platform port

## Goal

Port the 1995 3DO title Star Fighter (source: trapexit/3do-star-fighter) so it
builds and runs natively on **Windows, Linux and macOS**, using SDL for window,
input, audio and rendering. The original 3DO game code should stay as close to
the original as practical; platform differences live in a compatibility layer.
Windows is the primary development platform, but nothing may be Windows-only.

## Background you need

- The source is a 3DO (Portfolio OS) game. The original 3DO SDK ran on classic
  MacOS, so the files originally used CR line endings and MacRoman text.
  `convert_line_endings.py` (repo root) has already been run; everything text is
  now LF / UTF-8. Keep it that way (see `.gitattributes`).
- The repo also contains binaries and object files from the original archive
  (CELs, AIFC audio, Cinepak streams, executables, .o files). Never modify or
  "clean up" binary assets unless I ask.
- `3do-devkit` (github.com/trapexit/3do-devkit, cloned next to this repo at
  `../3do-devkit`) is a toolchain for building for real 3DO hardware. It is NOT
  the port build. Use it only as a read-only reference for 3DO API headers and
  documentation.
- Some code may be ARM assembly (`.s` files). It cannot run on a PC and needs a
  C replacement, checked against the original behaviour.

## Cross-platform hazards (check each during the inventory)

- **Endianness:** the 3DO's ARM is, as far as I know, big-endian, so CELs, AIFC
  audio and other binary data are probably big-endian. PCs and Apple Silicon are
  little-endian. Loading code needs explicit byte swapping through helper
  functions, never casts of raw buffers to structs. Verify against the code and
  data rather than assuming.
- **Integer and pointer sizes:** the original assumes 32-bit `int`, `long` and
  pointers. Use `<stdint.h>` fixed-width types, and look for pointer-to-int
  casts, `sizeof` assumptions, and structs read or written directly from files.
- **Paths and filenames:** classic MacOS paths are case-insensitive and contain
  spaces (e.g. `3DO cels`). Linux is case-sensitive. Route all file access
  through one path-resolving function in the shim layer that normalises
  separators and case. Prefer lowercase, space-free asset names in the port.
- **Fixed-point maths and timing:** keep the original fixed-point logic and
  frame timing semantics; do not "modernise" them without telling me.
- **Compiler differences:** MSVC, GCC and Clang disagree about old C. Prefer
  fixing the code to be standard C over compiler-specific flags.

## Environment

Windows (primary):
- Git for Windows, Python 3.12, CMake 4.x, Ninja
- Visual Studio 2026 Build Tools (MSVC; use "Developer PowerShell for VS")
- vcpkg at `C:\dev\vcpkg` (`VCPKG_ROOT` is set)

Linux test environment: WSL2 Ubuntu, with its own clone at
`~/dev/3do/star-fighter` and its own vcpkg at `~/vcpkg`. Never build from
`/mnt/c`.

Workspace layout (Windows):

    C:\dev\3do\
      3do-devkit\      reference only, never edit
      star-fighter\    this repo (fork of trapexit/3do-star-fighter)

Git: `origin` is my fork, `upstream` is trapexit/3do-star-fighter. `master`
mirrors upstream and stays untouched. All work happens on the `port` branch.

## Directory layout (confirm and expand after the inventory)

Original tree:
- `3DO cels/`, `Coded8bpp/`, `SF_Resources/`: assets and resources
- `SF3000/`, `StarUpdates/`, `StarUpdates2/`: game source and updates
- `Utility/`: miscellaneous tools
- `Notes On Final`, `cdrom.tcl`, `Star3000`, `StarLogo`: top-level files

New code (create as needed):

    port/
      CMakeLists.txt
      portfolio_compat/   3DO API replacements, platform-neutral C
      platform/           SDL-backed implementations (window, input, audio)
      NOTES.md            API inventory and decisions
    vcpkg.json            dependencies (SDL etc.)
    .github/workflows/    CI

TODO: after the inventory, replace the original-tree list with what each
directory actually contains.

## Build

- CMake + Ninja, dependencies through vcpkg manifest mode. Toolchain file:
  `$VCPKG_ROOT/scripts/buildsystems/vcpkg.cmake`.
- Windows: run from a VS Developer PowerShell, e.g.
  `cmake -S port -B port/build -G Ninja -DCMAKE_TOOLCHAIN_FILE="$env:VCPKG_ROOT/scripts/buildsystems/vcpkg.cmake"`
  then `cmake --build port/build`.
- Linux (WSL): the same, with `$VCPKG_ROOT` and a GCC or Clang toolchain.

TODO: replace with the exact working commands once the first build succeeds.

## Architecture rules

1. Do not edit original game files in place unless required to compile. Prefer
   the compatibility layer.
2. All 3DO API replacements live in `port/portfolio_compat/`. Mirror original
   function names and signatures so game code needs minimal changes.
3. Platform-specific code lives in `port/platform/` and only talks to SDL. No
   Win32, POSIX-only or macOS-only calls in shared or game code. If something
   platform-specific is unavoidable, isolate it behind a small interface and
   say so.
4. Game code must not include SDL or OS headers directly.
5. If a change to original game code is unavoidable, keep it small and mark it
   `/* PORT: reason */` so changes can be found later.
6. Do not delete original files; exclude them from the new build instead.
7. Keep new code standard C (state the C standard in CMake) unless I approve
   otherwise.

## Work order

1. Inventory every 3DO API call, header and OS service the game uses. Write the
   result to `port/NOTES.md` (call, where used, planned replacement), and note
   any endianness, integer-size and path issues found.
2. Create the CMake skeleton, `vcpkg.json` and CI (Windows, Ubuntu, macOS),
   then the stub shim layer, and get everything compiling against it.
3. Implement, in order: graphics (CEL rendering and frame display), input, audio
   (AIFC), video (Cinepak streams), file/CD-ROM access.
4. Replace any ARM assembly with C last, verifying against the original.
5. Test on a real run: boot to menu, start a mission, fly, shoot, exit cleanly.

## How I want you to work

- One stage at a time. Tell me the plan before large changes.
- Commit after each working stage with a clear message, on the `port` branch.
- Build after every non-trivial change and show me the compiler errors rather
  than guessing around them.
- After changes to shared code, check they would also build on Linux, or tell
  me what still needs testing there.
- When behaviour is uncertain (timing, fixed-point maths, CEL formats,
  endianness), say so and point to the code you based the decision on, rather
  than inventing details.
- Ask before adding dependencies, changing the build system, or touching binary
  assets.

## Definition of done

From a clean checkout the game builds with the documented commands on Windows,
Linux and macOS, CI is green on all three, and a full mission plays with
graphics, input and audio working.
