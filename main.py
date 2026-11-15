"""
MINDMISSION — Brain Training Arcade
A polished Pygame mini-game collection.

Controls:
- Mouse: navigate and play
- D: cycle difficulty on the home screen
- ESC: return to the previous screen / home
- F11: toggle fullscreen
- Q: quit from the home screen
"""

import asyncio
import json
import os
import random
import sys
import time
import pygame

pygame.init()

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------
WIDTH, HEIGHT = 720, 720
FPS = 60
TITLE = "MIND MISSION"
SAVE_FILE = "mindmission_stats.json"

FULLSCREEN = False
ignore_bootstrap_click = sys.platform == "emscripten"
display_surface = None
screen = None
clock = pygame.time.Clock()

# Theme
BG = (7, 11, 24)
PANEL = (15, 24, 43)
PANEL_HOVER = (23, 39, 65)
CYAN = (38, 220, 245)
BLUE = (65, 135, 255)
GREEN = (65, 240, 165)
WHITE = (238, 246, 255)
MUTED = (145, 164, 190)
RED = (255, 95, 115)
GOLD = (255, 205, 90)
BORDER = (36, 75, 105)

FONT = pygame.font.SysFont("arial", 22)
SMALL = pygame.font.SysFont("arial", 16)
MEDIUM = pygame.font.SysFont("arial", 30, bold=True)
BIG = pygame.font.SysFont("arial", 58, bold=True)
HUGE = pygame.font.SysFont("arial", 76, bold=True)

DIFFICULTIES = ("EASY", "MEDIUM", "HARD")
DIFFICULTY_INDEX = 0

# ---------------------------------------------------------------------------
# DISPLAY HELPERS
# The game renders to a stable square canvas, then scales that canvas into the
# browser's real drawing area. This keeps both the artwork and mouse targets
# aligned when Pygbag changes the canvas size to fit a viewer's window.
# ---------------------------------------------------------------------------
def _browser_canvas_size():
    if sys.platform == "emscripten":
        try:
            import platform as browser_platform
            canvas = browser_platform.window.canvas
            width, height = int(canvas.width), int(canvas.height)
            if width > 0 and height > 0:
                return width, height
        except (AttributeError, TypeError, ValueError):
            pass
    return WIDTH, HEIGHT


def set_display_size(output_size=None):
    global display_surface, screen
    if output_size is None:
        if sys.platform == "emscripten":
            output_size = _browser_canvas_size()
        elif FULLSCREEN:
            info = pygame.display.Info()
            output_size = (info.current_w, info.current_h)
        else:
            output_size = (WIDTH, HEIGHT)

    output_width = max(1, int(output_size[0]))
    output_height = max(1, int(output_size[1]))
    flags = pygame.RESIZABLE
    if FULLSCREEN and sys.platform != "emscripten":
        flags = pygame.FULLSCREEN
    display_surface = pygame.display.set_mode((output_width, output_height), flags)
    screen = pygame.Surface((WIDTH, HEIGHT)).convert()
    pygame.display.set_caption(TITLE)


set_display_size()


def present():
    output_width, output_height = display_surface.get_size()
    scale = min(output_width / WIDTH, output_height / HEIGHT)
    render_size = (max(1, round(WIDTH * scale)), max(1, round(HEIGHT * scale)))
    frame = screen if render_size == (WIDTH, HEIGHT) else pygame.transform.smoothscale(screen, render_size)
    display_surface.fill(BG)
    x = (output_width - render_size[0]) // 2
    y = (output_height - render_size[1]) // 2
    display_surface.blit(frame, (x, y))
    pygame.display.flip()


def to_logical_point(point):
    output_width, output_height = display_surface.get_size()
    scale = min(output_width / WIDTH, output_height / HEIGHT)
    x = (output_width - WIDTH * scale) / 2
    y = (output_height - HEIGHT * scale) / 2
    return ((point[0] - x) / scale, (point[1] - y) / scale)


def draw_text(surface, text, font, color, center=None, topleft=None, topright=None):
    image = font.render(str(text), True, color)
    rect = image.get_rect()
    if center is not None:
        rect.center = center
    elif topleft is not None:
        rect.topleft = topleft
    elif topright is not None:
        rect.topright = topright
    surface.blit(image, rect)
    return rect


def draw_wordmark(center_x, top, font, gap=10):
    first = font.render("MIND", True, WHITE)
    second = font.render("MISSION", True, CYAN)
    total_width = first.get_width() + gap + second.get_width()
    left = center_x - total_width // 2
    screen.blit(first, (left, top))
    screen.blit(second, (left + first.get_width() + gap, top))
    return pygame.Rect(left, top, total_width, max(first.get_height(), second.get_height()))


def draw_left_wordmark(left, top, font, gap=8):
    first = font.render("MIND", True, WHITE)
    second = font.render("MISSION", True, CYAN)
    screen.blit(first, (left, top))
    screen.blit(second, (left + first.get_width() + gap, top))


def draw_background():
    screen.fill(BG)
    # Subtle horizontal glow bands
    for y in range(0, HEIGHT, 4):
        shade = max(0, 13 - abs(HEIGHT // 2 - y) // 55)
        if shade:
            pygame.draw.line(screen, (7, 11 + shade, 25 + shade), (0, y), (WIDTH, y))


def draw_panel(rect, fill=PANEL, border=BORDER, radius=18, width=1):
    pygame.draw.rect(screen, fill, rect, border_radius=radius)
    pygame.draw.rect(screen, border, rect, width, border_radius=radius)


def draw_header(section, subtitle="TRAIN YOUR MIND"):
    draw_left_wordmark(32, 20, MEDIUM)
    draw_text(screen, section.upper(), SMALL, MUTED, topleft=(32, 62))
    draw_text(screen, subtitle, SMALL, MUTED, topright=(WIDTH - 32, 35))
    pygame.draw.line(screen, BORDER, (32, 91), (WIDTH - 32, 91), 1)


def draw_footer(message="ESC  •  BACK TO MENU"):
    draw_text(screen, message, SMALL, MUTED, center=(WIDTH // 2, HEIGHT - 24))


# ---------------------------------------------------------------------------
# PARTICLE BACKGROUND
# ---------------------------------------------------------------------------
class Particle:
    def __init__(self):
        self.x = random.uniform(0, WIDTH)
        self.y = random.uniform(0, HEIGHT)
        self.vx = random.uniform(-0.28, 0.28)
        self.vy = random.uniform(-0.28, 0.28)
        self.radius = random.choice((1, 1, 2))

    def update(self):
        self.x += self.vx
        self.y += self.vy
        if self.x < 0 or self.x > WIDTH:
            self.vx *= -1
        if self.y < 0 or self.y > HEIGHT:
            self.vy *= -1


particles = [Particle() for _ in range(65)]


def draw_particles():
    for particle in particles:
        particle.update()
        pygame.draw.circle(screen, (28, 120, 155),
                           (int(particle.x), int(particle.y)), particle.radius)
    # Keep the network effect subtle and lightweight
    for i, first in enumerate(particles):
        for second in particles[i + 1:]:
            dx = first.x - second.x
            dy = first.y - second.y
            distance_sq = dx * dx + dy * dy
            if distance_sq < 115 * 115:
                pygame.draw.line(screen, (17, 58, 85),
                                 (int(first.x), int(first.y)),
                                 (int(second.x), int(second.y)), 1)


# ---------------------------------------------------------------------------
# UI COMPONENTS
# ---------------------------------------------------------------------------
class Button:
    def __init__(self, rect, text, accent=CYAN, font=FONT):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.accent = accent
        self.font = font
        self.enabled = True
        self.focused = False

    def draw(self):
        hovered = self.rect.collidepoint(to_logical_point(pygame.mouse.get_pos())) and self.enabled
        active = (hovered or self.focused) and self.enabled
        fill = PANEL_HOVER if active else PANEL
        border = self.accent if active else BORDER
        draw_panel(self.rect, fill, border, 13, 3 if active else 1)
        text_color = WHITE if self.enabled else MUTED
        draw_text(screen, self.text, self.font, text_color, center=self.rect.center)

    def clicked(self, event):
        return (
            self.enabled
            and event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(to_logical_point(event.pos))
        )


def make_button(center_x, y, width, height, text, accent=CYAN, font=FONT):
    return Button((center_x - width // 2, y, width, height), text, accent, font)


# ---------------------------------------------------------------------------
# SAVE DATA
# ---------------------------------------------------------------------------
def load_stats():
    default = {
        "games_played": 0,
        "maze_wins": 0,
        "recall_wins": 0,
        "reaction_best": None,
        "recall_best_streak": 0,
    }
    try:
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, "r", encoding="utf-8") as file:
                saved = json.load(file)
            default.update(saved)
    except (OSError, json.JSONDecodeError):
        pass
    return default


stats = load_stats()


def save_stats():
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as file:
            json.dump(stats, file, indent=2)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# GLOBAL EVENT / NAVIGATION HELPERS
# ---------------------------------------------------------------------------
def handle_global_event(event):
    global FULLSCREEN
    if event.type == pygame.QUIT:
        # Browser canvas close events must not tear down SDL under the event loop.
        return
    if event.type == pygame.VIDEORESIZE:
        set_display_size((event.w, event.h))
        return True
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_F11:
            FULLSCREEN = not FULLSCREEN
            set_display_size()
            return True
    return False


async def wait_screen(title, message, color=GREEN, seconds=1.4):
    start = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start < seconds * 1000:
        for event in pygame.event.get():
            handle_global_event(event)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return
        draw_background()
        draw_particles()
        card = pygame.Rect(WIDTH // 2 - 260, HEIGHT // 2 - 100, 520, 200)
        draw_panel(card, PANEL, BORDER, 24, 2)
        draw_text(screen, title, BIG, color, center=(WIDTH // 2, HEIGHT // 2 - 35))
        draw_text(screen, message, FONT, MUTED, center=(WIDTH // 2, HEIGHT // 2 + 30))
        present()
        clock.tick(FPS)
        await asyncio.sleep(0)


# ---------------------------------------------------------------------------
# MAZE MISSION
# ---------------------------------------------------------------------------
def generate_maze(cols, rows):
    maze = [[1 for _ in range(cols)] for _ in range(rows)]
    stack = [(1, 1)]
    maze[1][1] = 0
    while stack:
        x, y = stack[-1]
        directions = [(2, 0), (-2, 0), (0, 2), (0, -2)]
        random.shuffle(directions)
        carved = False
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 1 <= nx < cols - 1 and 1 <= ny < rows - 1 and maze[ny][nx] == 1:
                maze[y + dy // 2][x + dx // 2] = 0
                maze[ny][nx] = 0
                stack.append((nx, ny))
                carved = True
                break
        if not carved:
            stack.pop()
    return maze


async def maze_game():
    global WIDTH, HEIGHT
    diff = DIFFICULTIES[DIFFICULTY_INDEX]
    cols, rows = {"EASY": (15, 11), "MEDIUM": (21, 15), "HARD": (27, 19)}[diff]
    maze = generate_maze(cols, rows)
    player = [1, 1]
    goal = [cols - 2, rows - 2]
    started = pygame.time.get_ticks()
    moves = 0

    while True:
        for event in pygame.event.get():
            handle_global_event(event)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return
                dx = dy = 0
                if event.key in (pygame.K_UP, pygame.K_w):
                    dy = -1
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    dy = 1
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    dx = -1
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    dx = 1
                nx, ny = player[0] + dx, player[1] + dy
                if (dx or dy) and 0 <= nx < cols and 0 <= ny < rows and maze[ny][nx] == 0:
                    player = [nx, ny]
                    moves += 1

        draw_background()
        draw_particles()
        draw_header("MAZE RUNNER", "CYAN: YOU  ·  GREEN: EXIT")
        area_w = min(WIDTH - 100, int((HEIGHT - 180) * cols / rows))
        area_h = min(HEIGHT - 160, int(area_w * rows / cols))
        cell = max(8, min(area_w // cols, area_h // rows))
        maze_w, maze_h = cell * cols, cell * rows
        ox, oy = (WIDTH - maze_w) // 2, 112 + (HEIGHT - 140 - maze_h) // 2
        draw_panel(pygame.Rect(ox - 10, oy - 10, maze_w + 20, maze_h + 20),
                   (10, 18, 34), BORDER, 14)

        for y in range(rows):
            for x in range(cols):
                color = (20, 37, 57) if maze[y][x] else (9, 16, 30)
                pygame.draw.rect(screen, color, (ox + x * cell, oy + y * cell, cell, cell))
        pygame.draw.rect(screen, GREEN, (ox + goal[0] * cell + 2, oy + goal[1] * cell + 2,
                                         cell - 4, cell - 4), border_radius=4)
        pygame.draw.rect(screen, CYAN, (ox + player[0] * cell + 2, oy + player[1] * cell + 2,
                                         cell - 4, cell - 4), border_radius=4)

        elapsed = (pygame.time.get_ticks() - started) // 1000
        status = pygame.Rect(WIDTH // 2 - 170, HEIGHT - 92, 340, 42)
        draw_panel(status, PANEL, BORDER, 12)
        draw_text(screen, f"TIME  {elapsed}s     MOVES  {moves}", SMALL, CYAN,
                  center=status.center)
        draw_footer("ARROW KEYS / WASD  •  ESC TO QUIT MISSION")
        present()
        clock.tick(FPS)
        await asyncio.sleep(0)

        if player == goal:
            stats["games_played"] += 1
            stats["maze_wins"] += 1
            save_stats()
            await wait_screen("MISSION COMPLETE", f"Exit found in {elapsed} seconds • {moves} moves")
            return


# ---------------------------------------------------------------------------
# REACTION MISSION
# ---------------------------------------------------------------------------
async def reaction_game():
    diff = DIFFICULTIES[DIFFICULTY_INDEX]
    target = {"EASY": 450, "MEDIUM": 300, "HARD": 200}[diff]
    phase = "ready"
    change_at = 0
    reaction_start = 0
    result = None

    def activate(now):
        nonlocal phase, change_at, reaction_start, result
        if phase == "ready":
            phase = "waiting"
            change_at = now + random.randint(1300, 3500)
        elif phase == "waiting":
            phase = "false_start"
        elif phase == "go":
            result = now - reaction_start
            stats["games_played"] += 1
            if stats["reaction_best"] is None or result < stats["reaction_best"]:
                stats["reaction_best"] = result
            save_stats()
            phase = "result"
        else:
            phase = "ready"
            result = None

    while True:
        now = pygame.time.get_ticks()
        for event in pygame.event.get():
            handle_global_event(event)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return
                if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                    activate(now)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                activate(now)

        if phase == "waiting" and now >= change_at:
            phase = "go"
            reaction_start = now

        draw_background()
        draw_particles()
        draw_header("REFLEX PROTOCOL", "WAIT FOR THE SIGNAL")

        card = pygame.Rect(WIDTH // 2 - 250, HEIGHT // 2 - 170, 500, 340)
        draw_panel(card, PANEL, BORDER, 24, 2)

        if phase == "ready":
            draw_text(screen, "REACTION TEST", BIG, WHITE, center=(WIDTH // 2, HEIGHT // 2 - 55))
            draw_text(screen, "CLICK OR PRESS SPACE TO BEGIN", FONT, CYAN,
                      center=(WIDTH // 2, HEIGHT // 2 + 35))
        elif phase == "waiting":
            draw_text(screen, "WAIT...", BIG, GOLD, center=(WIDTH // 2, HEIGHT // 2 - 35))
            draw_text(screen, "CLICK / SPACE ONLY WHEN THE SIGNAL TURNS GREEN", SMALL, MUTED,
                      center=(WIDTH // 2, HEIGHT // 2 + 35))
        elif phase == "go":
            pygame.draw.circle(screen, GREEN, (WIDTH // 2, HEIGHT // 2), 72)
            draw_text(screen, "CLICK NOW!", MEDIUM, WHITE,
                      center=(WIDTH // 2, HEIGHT // 2 + 115))
        elif phase == "false_start":
            draw_text(screen, "TOO EARLY!", BIG, RED, center=(WIDTH // 2, HEIGHT // 2 - 25))
            draw_text(screen, "You clicked before the signal.", FONT, MUTED,
                      center=(WIDTH // 2, HEIGHT // 2 + 40))
            draw_text(screen, "CLICK OR PRESS SPACE TO TRY AGAIN", SMALL, CYAN,
                      center=(WIDTH // 2, HEIGHT // 2 + 90))
        elif phase == "result":
            label = "ELITE REFLEX!" if result <= target else "GOOD ATTEMPT!"
            color = GREEN if result <= target else CYAN
            draw_text(screen, f"{result} ms", HUGE, color, center=(WIDTH // 2, HEIGHT // 2 - 50))
            draw_text(screen, label, MEDIUM, WHITE, center=(WIDTH // 2, HEIGHT // 2 + 30))
            draw_text(screen, f"Target for {diff.lower()}: {target} ms", SMALL, MUTED,
                      center=(WIDTH // 2, HEIGHT // 2 + 85))
            draw_text(screen, "CLICK / SPACE: RETRY     ESC: MENU", SMALL, CYAN,
                      center=(WIDTH // 2, HEIGHT // 2 + 125))

        draw_footer()
        present()
        clock.tick(FPS)
        await asyncio.sleep(0)


# ---------------------------------------------------------------------------
# MEMORY MISSION
# ---------------------------------------------------------------------------
async def recall_game():
    diff = DIFFICULTIES[DIFFICULTY_INDEX]
    length = {"EASY": 3, "MEDIUM": 4, "HARD": 5}[diff]
    symbols = ["APPLE", "BOOK", "STAR", "CROWN", "PLANET", "MUSIC", "ROCKET"]
    sequence = random.sample(symbols, length)
    options = random.sample(symbols, len(symbols))
    show_until = pygame.time.get_ticks() + (2600 if diff == "EASY" else 2200 if diff == "MEDIUM" else 1800)
    phase = "memorise"
    selected = []
    feedback = ""
    feedback_color = GREEN
    choice_focus = 0

    buttons = []
    cols = 3
    bw, bh, gap = 184, 62, 16
    total_w = cols * bw + (cols - 1) * gap
    start_x = (WIDTH - total_w) // 2
    for index, item in enumerate(options):
        x = start_x + (index % cols) * (bw + gap)
        y = 310 + (index // cols) * (bh + gap)
        buttons.append((item, Button((x, y, bw, bh), f"{index + 1}  ·  {item}", BLUE, SMALL)))

    def choose_item(item):
        nonlocal phase, feedback, feedback_color
        if phase != "answer" or item in selected:
            return
        selected.append(item)
        if len(selected) == length:
            correct = selected == sequence
            stats["games_played"] += 1
            if correct:
                stats["recall_wins"] += 1
                stats["recall_best_streak"] = max(stats["recall_best_streak"], length)
            save_stats()
            phase = "result"
            feedback = "MEMORY MASTER!" if correct else "NOT QUITE!"
            feedback_color = GREEN if correct else RED

    while True:
        now = pygame.time.get_ticks()
        if phase == "memorise" and now >= show_until:
            phase = "answer"

        for event in pygame.event.get():
            handle_global_event(event)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return
                if phase == "result" and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    return
                if phase == "answer":
                    number_keys = (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
                                   pygame.K_5, pygame.K_6, pygame.K_7)
                    if event.key in number_keys:
                        index = number_keys.index(event.key)
                        if index < len(options):
                            choice_focus = index
                            choose_item(options[index])
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        choice_focus = max(0, choice_focus - 1)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        choice_focus = min(len(options) - 1, choice_focus + 1)
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        choice_focus = max(0, choice_focus - cols)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        choice_focus = min(len(options) - 1, choice_focus + cols)
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                        choose_item(options[choice_focus])

            if phase == "answer" and event.type == pygame.MOUSEBUTTONDOWN:
                for index, (item, button) in enumerate(buttons):
                    if button.clicked(event):
                        choice_focus = index
                        choose_item(item)

        draw_background()
        draw_particles()
        draw_header("MEMORY MATRIX", "REMEMBER THE ORDER")

        if phase == "memorise":
            draw_text(screen, "MEMORISE THIS SEQUENCE", MEDIUM, WHITE,
                      center=(WIDTH // 2, HEIGHT // 2 - 130))
            for i, item in enumerate(sequence):
                box = pygame.Rect(WIDTH // 2 - 180, HEIGHT // 2 - 75 + i * 54, 360, 44)
                draw_panel(box, PANEL, CYAN, 10)
                draw_text(screen, f"{i + 1}.  {item}", FONT, CYAN, center=box.center)
            remaining = max(0, (show_until - now) // 1000 + 1)
            draw_text(screen, f"Memorise quickly  ·  {remaining}", SMALL, MUTED,
                      center=(WIDTH // 2, HEIGHT - 65))
        elif phase == "answer":
            draw_text(screen, "PICK THE ITEMS IN ORDER", MEDIUM, WHITE,
                      center=(WIDTH // 2, 192))
            draw_text(screen, f"PROGRESS  {len(selected)} / {length}", SMALL, CYAN,
                      center=(WIDTH // 2, 226))
            for index, (item, button) in enumerate(buttons):
                button.enabled = item not in selected
                button.focused = index == choice_focus and button.enabled
                button.draw()
            draw_text(screen, "CLICK A TILE OR PRESS 1–7  ·  ARROWS MOVE  ·  ENTER SELECT",
                      SMALL, MUTED, center=(WIDTH // 2, 574))
            draw_text(screen, "ORDER  " + ("  →  ".join(selected) if selected else "—"),
                      SMALL, CYAN, center=(WIDTH // 2, 604))
        else:
            draw_text(screen, feedback, BIG, feedback_color,
                      center=(WIDTH // 2, HEIGHT // 2 - 65))
            draw_text(screen, "Correct order: " + "  →  ".join(sequence), FONT, WHITE,
                      center=(WIDTH // 2, HEIGHT // 2 + 10))
            draw_text(screen, "SPACE / ENTER: PLAY AGAIN  •  ESC: MENU", SMALL, CYAN,
                      center=(WIDTH // 2, HEIGHT // 2 + 75))

        draw_footer()
        present()
        clock.tick(FPS)
        await asyncio.sleep(0)


# ---------------------------------------------------------------------------
# HOME SCREEN
# ---------------------------------------------------------------------------
async def home_screen():
    global DIFFICULTY_INDEX, ignore_bootstrap_click
    center = WIDTH // 2
    buttons = [
        make_button(center, 300, 360, 62, "MAZE RUNNER", CYAN, MEDIUM),
        make_button(center, 378, 360, 62, "REFLEX PROTOCOL", BLUE, MEDIUM),
        make_button(center, 456, 360, 62, "MEMORY MATRIX", GREEN, MEDIUM),
        make_button(center, 532, 176, 48, "QUIT", RED, FONT),
    ]
    diff_button = Button((center - 120, 215, 240, 42),
                         f"DIFFICULTY: {DIFFICULTIES[DIFFICULTY_INDEX]}", GOLD, SMALL)
    focus_index = 0

    while True:
        center = WIDTH // 2
        buttons[0].rect.center = (center, 300)
        buttons[1].rect.center = (center, 378)
        buttons[2].rect.center = (center, 456)
        buttons[3].rect.center = (center, 532)
        diff_button.rect.center = (center, 236)
        for event in pygame.event.get():
            handle_global_event(event)
            if event.type == pygame.MOUSEBUTTONDOWN and ignore_bootstrap_click:
                ignore_bootstrap_click = False
                continue
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_d, pygame.K_TAB):
                    DIFFICULTY_INDEX = (DIFFICULTY_INDEX + 1) % len(DIFFICULTIES)
                elif event.key == pygame.K_q:
                    return
                elif event.key in (pygame.K_UP, pygame.K_w):
                    focus_index = (focus_index - 1) % len(buttons)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    focus_index = (focus_index + 1) % len(buttons)
                elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                    index = event.key - pygame.K_1
                    focus_index = index
                    if index == 0:
                        await maze_game()
                    elif index == 1:
                        await reaction_game()
                    else:
                        await recall_game()
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    if focus_index == 0:
                        await maze_game()
                    elif focus_index == 1:
                        await reaction_game()
                    elif focus_index == 2:
                        await recall_game()
                    else:
                        save_stats()
                        return
            if diff_button.clicked(event):
                DIFFICULTY_INDEX = (DIFFICULTY_INDEX + 1) % len(DIFFICULTIES)
            if buttons[0].clicked(event):
                focus_index = 0
                await maze_game()
            elif buttons[1].clicked(event):
                focus_index = 1
                await reaction_game()
            elif buttons[2].clicked(event):
                focus_index = 2
                await recall_game()
            elif buttons[3].clicked(event):
                save_stats()
                return

        diff_button.text = f"DIFFICULTY: {DIFFICULTIES[DIFFICULTY_INDEX]}"

        draw_background()
        draw_particles()

        draw_wordmark(center, 62, HUGE, gap=24)
        draw_text(screen, "A BRAIN-TRAINING ARCADE", SMALL, MUTED,
                  center=(center, 169))
        draw_text(screen, "Choose a mission. Challenge your mind. Beat your best.",
                  FONT, WHITE, center=(center, 193))

        diff_button.draw()
        for index, button in enumerate(buttons):
            button.focused = index == focus_index
            button.draw()

        panel = pygame.Rect(32, 626, WIDTH - 64, 60)
        draw_panel(panel, (10, 18, 34), BORDER, 14)
        best = stats["reaction_best"]
        best_text = f"{best} ms" if best is not None else "—"
        summary = (
            f"MISSIONS {stats['games_played']}   •   MAZE {stats['maze_wins']}   •   "
            f"MEMORY {stats['recall_wins']}   •   REACTION {best_text}"
        )
        draw_text(screen, summary, SMALL, MUTED, center=panel.center)
        draw_text(screen, "↑ / ↓ SELECT   •   ENTER OPEN   •   1–3 QUICK PLAY",
                  SMALL, CYAN, center=(center, 582))
        draw_text(screen, "D / TAB: DIFFICULTY   •   F11: FULL SCREEN   •   Q: QUIT",
                  SMALL, MUTED, center=(center, 603))

        present()
        clock.tick(FPS)
        await asyncio.sleep(0)


async def main():
    await home_screen()

asyncio.run(main())
