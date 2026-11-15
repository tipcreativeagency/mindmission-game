# MINDMISSION browser presentation

## Visual system

Keep the game's arcade identity: deep navy surfaces, cyan and blue mission accents, green success states, gold difficulty cues, and quiet network linework. The browser page, loading state, and letterboxed canvas all use the same navy background so the game reads as one centered experience.

Use a stable 720 × 720 layout rendered to a 1440 × 1440 backing surface for high-density screens. Keep the canvas square, centered, and sized to the smaller of the available viewport width and height. Apply the same scale and offset to pointer and touch input. Never stretch or crop gameplay controls when the browser resizes.

The main wordmark is a centered two-part lockup: white “MIND”, a visible 20–24 px gap, and cyan “MISSION”. Mission headers use the same words with a smaller gap. Keep text off the border and maintain clear vertical space between titles, instructions, and controls.

## Interaction principles

- Keep the three missions visually distinct while sharing the same header, panels, buttons, and footer.
- Make the complete Memory Matrix choice grid fit inside the canvas at every supported size.
- Show a visible focus outline for keyboard-selected buttons. Support arrow keys and Enter on the home screen, and mouse or keyboard input inside each mission.
- Keep mission navigation and sound controls available on touch screens. Maze Runner has a large on-screen four-way pad; other missions use tap targets already built into their gameplay.
- Use brief, quiet synthesized sound effects for actions and feedback. Keep an on-screen sound toggle visible while playing.
- Preserve readable text and controls when the square canvas is scaled down. The game canvas itself remains the interactive surface; avoid decorative browser chrome around it.
- Keep the existing game rules, scores, and mission content unchanged while polishing layout and feedback.
