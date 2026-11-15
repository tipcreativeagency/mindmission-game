# MINDMISSION

A browser-playable build of the Python/Pygame game, plus its Pygbag-compatible source.

## Play

Open the published GitHub Pages site in a modern desktop browser. The game loads from the files in this repository. It may take a short while on first load while the browser runtime initializes.

## Run locally

Serve this folder over HTTP (for example, `python3 -m http.server 8000`) and open `http://localhost:8000/`. Opening `index.html` directly as a file may not work because browsers restrict loading the game bundle from disk.

## Source and build

`main.py` is the browser-ready Pygame source. It uses Pygbag's asynchronous entry point so the game loop can yield to the browser. The web runtime and game bundle are included in the root because GitHub Pages serves static files.

The `.apk` filename is part of Pygbag's web bundle convention used by `index.html`; it is not an installable Android APK. A native Android APK requires a separate Android packaging workflow.
