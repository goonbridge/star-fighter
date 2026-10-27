# Star Fighter (3DO) -> Windows port

## Goal

Port the 1995 3DO title Star Fighter (source: trapexit/3do-star-fighter) to
build and run natively on Windows, using SDL2 for window, input, audio and
rendering. The 3DO game code should stay as close to the original as
practical; the platform differences live in a compatibility layer.

## Background you need

- The source is a 3DO (Portfolio OS) game. The original 3DO SDK ran on classic
  MacOS, so the source files originally used CR line endings and MacRoman text.
  Run `convert_line_endings.py` (repo root) once; after that everything is LF /
  UTF-8.
- The repo also contains binaries and object files from the original archive
  (CELs, AIFC audio, Cinepak streams, executables, .o files). Never modify or
  "clean up" binary assets unless I ask.
- `3do-devkit` (github.com/trapexit/3do-devkit) is a build toolchain for real
  3DO hardware. It is NOT the Windows build. Use it only as a reference for 3DO
  API headers and documentation.
- Some code may be ARM assembly (`.s` files). It cannot run on Windows and
  needs a C replacement, checked against the original behaviour.

## Directory layout (from the repo root; confirm and expand after the inventory)

- `3DO cels/`, `Coded8bpp/`, `SF_Resources/`: assets and resources
- `SF3000/`, `StarUpdates/`, `StarUpdates2/`: game source and updates
- `Utility/`: miscellaneous tools
- `Notes On Final`, `cdrom.tcl`, `Star3000`, `StarLogo`: top-level files

TODO: after the inventory step, replace this section with what each directory
actually contains.

## Toolchain

- Windows 10/11, Visual Studio Build Tools (MSVC) or MinGW-w64
- CMake (new build lives in `port/`, not in the original tree)
- SDL2
- Git; all work happens on the `windows-port` branch

TODO: record exact versions and the configure/build commands here once chosen,
e.g. `cmake -S port -B port/build && cmake --build port/build`.

## Architecture rules

1. Do not edit original game files in place unless the change is required to
   compile. Prefer a compatibility layer.
2. Put all 3DO API replacements in `port/portfolio_compat/`. Mirror the original
   function names and signatures so game code needs minimal changes.
3. Keep platform-specific code (SDL2, Win32) inside `port/`. Game code must not
   include SDL or Windows headers directly.
4. If a change to original game code is unavoidable, make it small, and mark it
   with a `/* PORT: reason */` comment so changes can be found later.
5. Do not delete original files; leave them in place and exclude them from the
   new build instead.

## Work order

1. Inventory every 3DO API call, header and OS service the game uses. Write the
   result to `port/NOTES.md` (call name, where used, planned replacement).
2. Create the stub shim layer and get the whole codebase compiling against it.
3. Implement, in order: graphics (CEL rendering and frame display), input,
   audio (AIFC), video (Cinepak streams), file/CD-ROM access.
4. Replace any ARM assembly with C last, verifying against the original.
5. Test on a real run: boot to menu, start a mission, fly, shoot, exit cleanly.

## How I want you to work

- One stage at a time. Tell me the plan before large changes.
- Commit after each working stage with a clear message.
- Build after every non-trivial change and show me the compiler errors rather
  than guessing around them.
- When behaviour is uncertain (timing, fixed-point maths, CEL formats), say so
  and point to the code you based the decision on, rather than inventing
  details.
- Ask before adding new dependencies or changing the build system.

## Definition of done

The game builds from a clean checkout with the documented commands, launches
on Windows, and plays a full mission with graphics, input and audio working.
