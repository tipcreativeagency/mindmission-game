# MINDMISSION

A browser-playable build of the Python/Pygame game, plus its Pygbag-compatible source.

## Play

Open the published GitHub Pages site in a modern browser on desktop or mobile. The square game view adapts to the available screen and renders at high density. A first visit may take a short while while the browser runtime initializes.

On touch screens, use the four on-screen arrows to move in Maze Runner, tap anywhere to play Reflex Protocol, and tap the Memory Matrix tiles in order. Each mission has a menu button and a sound-effects toggle. On desktop, keyboard controls remain available.

## Run locally

Serve this folder over HTTP (for example, `python3 -m http.server 8000`) and open `http://localhost:8000/`. Opening `index.html` directly as a file may not work because browsers restrict loading the game bundle from disk.

## Source and build

`main.py` is the browser-ready Pygame source. It uses Pygbag's asynchronous entry point so the game loop can yield to the browser. The web runtime and game bundle are included in the root because GitHub Pages serves static files.

The versioned `.apk` filename is part of Pygbag's web bundle convention used by `index.html`; it is not an installable Android APK. The archive name is bumped when publishing game updates so mobile browsers do not reuse an older cached bundle. A native Android APK requires a separate Android packaging workflow.
