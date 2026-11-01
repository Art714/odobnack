import pygame
import random
import math
import sys
from collections import deque

pygame.init()

# ============ НАСТРОЙКИ ============
WIDTH, HEIGHT = 1100, 750
FPS = 60

BLACK = (0, 0, 0)
SKY_NIGHT = (8, 10, 25)
GRASS_DARK = (22, 45, 28)
GRASS_LIGHT = (28, 55, 32)
WALL_BRICK = (80, 60, 50)
WALL_BRICK_LIGHT = (110, 85, 70)
WALL_BRICK_DARK = (50, 35, 30)
MORTAR = (40, 35, 35)
FLOOR_WOOD = (90, 60, 40)
FLOOR_WOOD_LIGHT = (115, 80, 55)
FLOOR_WOOD_DARK = (60, 40, 25)
FLOOR_STONE = (65, 65, 70)
FLOOR_STONE_LIGHT = (90, 90, 95)
FLOOR_STONE_DARK = (45, 45, 50)
YARD_COLOR = (50, 70, 45)

PART_COLOR = (255, 215, 0)
PART_HELI = (100, 255, 150)
DOOR_COLOR = (80, 160, 255)
DOOR_GLOW = (120, 200, 255)
ACID_SHOTGUN = (200, 255, 0)
ACID_HELI = (0, 255, 100)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Особняк")
clock = pygame.time.Clock()

font = pygame.font.SysFont("arial", 20, bold=True)
med_font = pygame.font.SysFont("arial", 26, bold=True)
big_font = pygame.font.SysFont("arial", 64, bold=True)
hint_font = pygame.font.SysFont("arial", 14)
tiny_font = pygame.font.SysFont("arial", 10, bold=True)

TILE = 48

SHOTGUN_TOTAL = 3
HELI_TOTAL = 12
AMMO_TOTAL = 5
AMMO_PER_SHOTGUN = 1

MAP_W, MAP_H = 41, 29


# ============ ГЕНЕРАЦИЯ УРОВНЕЙ ============
def make_fixed_room_map():
    g = [['1'] * MAP_W for _ in range(MAP_H)]
    cols, rows = 3, 3
    cell_w = MAP_W // cols
    cell_h = MAP_H // rows

    rooms = []
    for row in range(rows):
        for col in range(cols):
            rx1 = col * cell_w + 3
            ry1 = row * cell_h + 3
            rx2 = (col + 1) * cell_w - 3
            ry2 = (row + 1) * cell_h - 3
            rooms.append((rx1, ry1, rx2, ry2))

    for (x1, y1, x2, y2) in rooms:
        for y in range(y1, y2):
            for x in range(x1, x2):
                if 0 <= y < MAP_H and 0 <= x < MAP_W: g[y][x] = '0'

    for row in range(rows):
        for col in range(cols):
            idx = row * cols + col
            room = rooms[idx]
            cx = (room[0] + room[2]) // 2
            cy = (room[1] + room[3]) // 2

            if col < cols - 1:
                right = rooms[row * cols + col + 1]
                for x in range(room[2] - 1, right[0] + 1):
                    for dy in range(-1, 2):
                        if 0 <= cy + dy < MAP_H and 0 <= x < MAP_W: g[cy + dy][x] = '0'

            if row < rows - 1:
                below = rooms[(row + 1) * cols + col]
                bcy = (below[1] + below[3]) // 2
                for y in range(room[3] - 1, below[1] + 1):
                    for dx in range(-1, 2):
                        if 0 <= y < MAP_H and 0 <= cx + dx < MAP_W: g[y][cx + dx] = '0'

    return [''.join(row) for row in g]


def make_street_map():
    W, H = MAP_W, MAP_H
    g = [['1'] * W for _ in range(H)]
    for y in range(4, H - 4):
        for x in range(4, W - 4): g[y][x] = 'Y'
    buildings = [(6, 6, 10, 10), (28, 6, 32, 10), (6, 18, 10, 22), (28, 18, 32, 22)]
    for (x1, y1, x2, y2) in buildings:
        for y in range(y1, y2):
            for x in range(x1, x2):
                if 0 <= y < H and 0 <= x < W: g[y][x] = '1'
    g[H // 2][W // 2] = '5'
    return [''.join(row) for row in g]


def find_reachable_cells(grid, start_x, start_y):
    g = grid
    visited = set()
    q = [(start_x, start_y)]
    visited.add((start_x, start_y))
    while q:
        cx, cy = q.pop(0)
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < len(g[0]) and 0 <= ny < len(g):
                if g[ny][nx] != '1' and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    q.append((nx, ny))
    return visited


def place_special_cells(grid, specials):
    g = [list(row) for row in grid]
    all_free = []
    for y in range(len(g)):
        for x in range(len(g[0])):
            if g[y][x] == '0': all_free.append((x, y))
    if not all_free: return [''.join(row) for row in g]
    sx, sy = all_free[0]
    reachable = find_reachable_cells(g, sx, sy)
    free = [c for c in all_free if c in reachable]
    random.shuffle(free)
    for char, count in specials.items():
        for _ in range(count):
            if not free: break
            x, y = free.pop()
            g[y][x] = char
    return [''.join(row) for row in g]


def generate_levels():
    global MAPS, FLOOR1_MAP, FLOOR2_MAP, BASEMENT_MAP, STREET_MAP
    STREET_MAP = make_street_map()

    f1 = make_fixed_room_map()
    f1 = place_special_cells(f1, {'4': 1, '3': 1, '2': 1})
    FLOOR1_MAP = f1

    f2 = make_fixed_room_map()
    f2 = place_special_cells(f2, {'3': 1, '2': 1})
    FLOOR2_MAP = f2

    b = make_fixed_room_map()
    b = place_special_cells(b, {'2': 1, '4': 1})
    BASEMENT_MAP = b

    MAPS = {
        "street": {"grid": STREET_MAP, "floor": "grass", "wall": "fence"},
        "floor1": {"grid": FLOOR1_MAP, "floor": "wood", "wall": "brick"},
        "floor2": {"grid": FLOOR2_MAP, "floor": "wood", "wall": "brick"},
        "basement": {"grid": BASEMENT_MAP, "floor": "stone", "wall": "stone"},
    }


MAPS = {}
generate_levels()


# ============ ОТРИСОВКА ТЕКСТУР ============
def draw_brick_wall(surf, rect, seed):
    surf.fill(MORTAR, rect)
    brick_h, brick_w = 12, 24
    for y in range(0, TILE, brick_h):
        off = 0 if (y // brick_h) % 2 == 0 else brick_w // 2
        for x in range(-off, TILE, brick_w):
            br = pygame.Rect(rect.x + x + 1, rect.y + y + 1, brick_w - 2, brick_h - 2).clip(rect)
            if br.w > 0 and br.h > 0:
                rng = random.Random(seed + x * 31 + y * 17)
                base_col = rng.choice([WALL_BRICK, WALL_BRICK_LIGHT, WALL_BRICK_DARK])
                pygame.draw.rect(surf, base_col, br)
                pygame.draw.line(surf, WALL_BRICK_LIGHT, (br.x, br.y), (br.right, br.y), 1)
                pygame.draw.line(surf, WALL_BRICK_DARK, (br.x, br.bottom - 1), (br.right, br.bottom - 1), 1)


def draw_stone_wall(surf, rect, seed):
    surf.fill(FLOOR_STONE_DARK, rect)
    rng = random.Random(seed)
    for _ in range(8):
        rx = rect.x + rng.randint(2, TILE - 18)
        ry = rect.y + rng.randint(2, TILE - 14)
        rw = rng.randint(10, 18)
        rh = rng.randint(8, 14)
        c = tuple(max(0, min(255, base + rng.randint(-20, 20))) for base in FLOOR_STONE)
        pygame.draw.rect(surf, c, (rx, ry, rw, rh))
        pygame.draw.rect(surf, FLOOR_STONE_LIGHT, (rx, ry, rw, 1))
    pygame.draw.rect(surf, (110, 110, 115), (rect.x, rect.y, TILE, 3))


def draw_fence(surf, rect, seed):
    surf.fill((30, 20, 15), rect)
    for x in range(0, TILE, 12):
        pygame.draw.rect(surf, (65, 45, 30), (rect.x + x, rect.y, 10, TILE))
        pygame.draw.rect(surf, (85, 60, 40), (rect.x + x, rect.y, 3, TILE))
    pygame.draw.rect(surf, (90, 65, 45), (rect.x, rect.y, TILE, 4))


def draw_wood_floor(surf, rect, seed):
    surf.fill(FLOOR_WOOD, rect)
    rng = random.Random(seed)
    for y in range(0, TILE, 12):
        pygame.draw.line(surf, FLOOR_WOOD_DARK, (rect.x, rect.y + y), (rect.right, rect.y + y), 1)
        pygame.draw.line(surf, FLOOR_WOOD_LIGHT, (rect.x, rect.y + y + 1), (rect.right, rect.y + y + 1), 1)
    if rng.random() < 0.2:
        cx = rect.x + rng.randint(5, TILE - 5)
        cy = rect.y + rng.randint(5, TILE - 5)
        pygame.draw.ellipse(surf, FLOOR_WOOD_DARK, (cx, cy, 6, 3))


def draw_stone_floor(surf, rect, seed):
    surf.fill(FLOOR_STONE, rect)
    pygame.draw.rect(surf, FLOOR_STONE_DARK, rect, 1)
    pygame.draw.line(surf, FLOOR_STONE_LIGHT, (rect.x + 1, rect.y + 1), (rect.right - 1, rect.y + 1), 1)


def draw_grass(surf, rect, seed):
    surf.fill(GRASS_DARK, rect)
    rng = random.Random(seed)
    for _ in range(3):
        gx = rect.x + rng.randint(2, TILE - 2)
        gy = rect.y + rng.randint(2, TILE - 2)
        pygame.draw.line(surf, (35, 60, 40), (gx, gy), (gx, gy - 4), 1)


def draw_yard(surf, rect, seed):
    surf.fill(YARD_COLOR, rect)
    rng = random.Random(seed)
    for _ in range(2):
        px = rect.x + rng.randint(2, TILE - 2)
        py = rect.y + rng.randint(2, TILE - 2)
        pygame.draw.circle(surf, (60, 80, 55), (px, py), 1)


def draw_stairs(surf, rect, is_up):
    col_main = (140, 100, 60) if is_up else (100, 70, 40)
    col_light = (180, 140, 100) if is_up else (140, 100, 70)
    for i in range(4):
        step_rect = pygame.Rect(rect.x + i * 4, rect.y + i * 4, rect.w - i * 8, rect.h - i * 8)
        pygame.draw.rect(surf, col_main, step_rect)
        pygame.draw.rect(surf, col_light, (step_rect.x, step_rect.y, step_rect.w, 2))
    t = hint_font.render("↑" if is_up else "↓", True, (255, 255, 220))
    surf.blit(t, (rect.centerx - t.get_width() // 2, rect.centery - t.get_height() // 2))


def draw_circular_entrance(surf, rect):
    cx = rect.centerx;
    cy = rect.centery
    pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 300)
    glow_radius = int(40 + pulse * 15)
    glow = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
    for layer in range(4, 0, -1):
        alpha = int(40 + pulse * 30) // layer
        r = glow_radius - layer * 4
        pygame.draw.circle(glow, (*DOOR_COLOR, alpha), (glow_radius, glow_radius), r)
    surf.blit(glow, (cx - glow_radius, cy - glow_radius))
    pygame.draw.circle(surf, (60, 60, 60), (cx, cy), 28)
    pygame.draw.circle(surf, (100, 100, 100), (cx, cy), 28, 3)
    pygame.draw.circle(surf, (30, 30, 40), (cx, cy), 22)
    pygame.draw.line(surf, (120, 80, 50), (cx, cy - 22), (cx, cy + 22), 3)
    pygame.draw.circle(surf, (255, 220, 100), (cx - 6, cy), 3)
    pygame.draw.circle(surf, (255, 220, 100), (cx + 6, cy), 3)
    t = hint_font.render("ВХОД", True, (200, 220, 255))
    surf.blit(t, (cx - t.get_width() // 2, cy - 45))


# ============ КЛАССЫ ЖИВОТНЫХ ============
class BaseAnimal:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.path = []
        self.path_timer = 0
        self.anim = 0
        self.facing_left = False
        self.state = "patrol"
        self.target = (x, y)

    def find_path(self, tx, ty):
        g = MAPS[current_level]["grid"]
        sx, sy = int(self.x // TILE), int(self.y // TILE)
        gx, gy = int(tx // TILE), int(ty // TILE)
        if not (0 <= gx < len(g[0]) and 0 <= gy < len(g)): return []
        if g[gy][gx] == '1': return []

        q = deque([(sx, sy)])
        visited = {(sx, sy): None}
        while q:
            cx, cy = q.popleft()
            if (cx, cy) == (gx, gy): break
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < len(g[0]) and 0 <= ny < len(g) and g[ny][nx] != '1' and (nx, ny) not in visited:
                    visited[(nx, ny)] = (cx, cy)
                    q.append((nx, ny))

        if (gx, gy) not in visited: return []
        path = []
        cur = (gx, gy)
        while cur is not None:
            path.append((cur[0] * TILE + TILE // 2, cur[1] * TILE + TILE // 2))
            cur = visited[cur]
        path.reverse()
        return path

    def pick_random_patrol(self):
        for _ in range(30):
            tx = random.randint(1, len(MAPS[current_level]["grid"][0]) - 2) * TILE + TILE // 2
            ty = random.randint(1, len(MAPS[current_level]["grid"]) - 2) * TILE + TILE // 2
            if not is_wall_px(tx, ty):
                self.target = (tx, ty)
                self.path_timer = 0
                return

    def move_along_path(self, dt, speed):
        if not self.path: return
        tx, ty = self.path[0]
        dx, dy = tx - self.x, ty - self.y
        d = math.hypot(dx, dy)
        if d < 10:
            self.path.pop(0)
        else:
            self.x += dx / d * speed * dt
            self.y += dy / d * speed * dt
            if abs(dx) > 0.5 or abs(dy) > 0.5:
                if dx < -0.5:
                    self.facing_left = True
                elif dx > 0.5:
                    self.facing_left = False


class Dog(BaseAnimal):
    def __init__(self, x, y):
        super().__init__(x, y)

    def update(self, dt, player_x, player_y, speed, delay, stun):
        if delay > 0 or stun > 0: return
        self.anim += dt
        dist = math.hypot(player_x - self.x, player_y - self.y)
        sees = dist < 250

        if sees:
            self.state = "chase"
            target_pos = (player_x, player_y)
        else:
            self.state = "patrol"
            if math.hypot(self.target[0] - self.x, self.target[1] - self.y) < 30:
                self.pick_random_patrol()
            target_pos = self.target

        self.path_timer -= dt
        if self.path_timer <= 0:
            self.path = self.find_path(target_pos[0], target_pos[1])
            self.path_timer = 0.3

        sp = speed if self.state == "chase" else speed * 0.5
        self.move_along_path(dt, sp)

    def draw(self, surf, cam_x, cam_y, stun):
        sx = int(self.x - cam_x);
        sy = int(self.y - cam_y)
        flip = self.facing_left

        def fx(offset):
            return sx + (offset if not flip else -offset)

        shadow = pygame.Surface((70, 20), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 130), (0, 0, 70, 20))
        surf.blit(shadow, (sx - 35, sy + 14))

        step = math.sin(self.anim * 14) * 5
        # Задние лапы
        pygame.draw.ellipse(surf, (60, 15, 15), (fx(-16 + step * 0.5), sy + 10, 8, 16))
        pygame.draw.ellipse(surf, (100, 25, 25), (fx(-10 - step * 0.5), sy + 10, 8, 16))

        # Тело
        pygame.draw.ellipse(surf, (60, 15, 15), (fx(-24), sy - 12, 46, 28))
        pygame.draw.ellipse(surf, (100, 25, 25), (fx(-22), sy - 10, 42, 24))
        pygame.draw.ellipse(surf, (140, 45, 40), (fx(-18), sy - 10, 34, 10))

        # Передние лапы
        pygame.draw.ellipse(surf, (60, 15, 15), (fx(12 - step * 0.5), sy + 10, 8, 16))
        pygame.draw.ellipse(surf, (100, 25, 25), (fx(18 + step * 0.5), sy + 10, 8, 16))

        # Голова
        head_x = fx(30)
        head_y = sy - 16
        pygame.draw.circle(surf, (60, 15, 15), (head_x, head_y), 16)
        pygame.draw.circle(surf, (100, 25, 25), (head_x, head_y), 14)

        # Уши
        pygame.draw.polygon(surf, (60, 15, 15), [(fx(22), head_y - 10), (fx(18), head_y - 28), (fx(30), head_y - 14)])
        pygame.draw.polygon(surf, (100, 25, 25), [(fx(34), head_y - 12), (fx(38), head_y - 30), (fx(44), head_y - 10)])

        # Морда
        muzzle_x = fx(42)
        pygame.draw.ellipse(surf, (60, 15, 15), (muzzle_x - 10, head_y + 2, 22, 14))
        pygame.draw.ellipse(surf, (100, 25, 25), (muzzle_x - 8, head_y + 4, 18, 10))
        pygame.draw.circle(surf, (10, 5, 5), (fx(48), head_y + 6), 4)

        # Клыки
        pygame.draw.ellipse(surf, (30, 0, 0), (muzzle_x - 8, head_y + 12, 16, 6))
        pygame.draw.polygon(surf, (240, 240, 230),
                            [(fx(38), head_y + 12), (fx(40), head_y + 20), (fx(42), head_y + 12)])
        pygame.draw.polygon(surf, (240, 240, 230),
                            [(fx(44), head_y + 12), (fx(46), head_y + 20), (fx(48), head_y + 12)])

        # Глаза
        eye_x = fx(36)
        eye_y = head_y - 2
        if self.state == "chase":
            pygame.draw.circle(surf, (255, 50, 50), (eye_x, eye_y), 5)
            pygame.draw.circle(surf, (255, 200, 200), (eye_x - 1, eye_y - 1), 2)
        else:
            pygame.draw.circle(surf, (255, 220, 40), (eye_x, eye_y), 5)
            pygame.draw.ellipse(surf, (20, 0, 0), (eye_x - 1, eye_y - 3, 2, 6))

        if stun > 0:
            for i in range(4):
                ang = pygame.time.get_ticks() / 200 + i * 1.57
                sx_off = head_x + math.cos(ang) * 20
                sy_off = head_y - 25 + math.sin(ang) * 5
                pygame.draw.circle(surf, (255, 255, 100), (int(sx_off), int(sy_off)), 3)


class Cat(BaseAnimal):
    def __init__(self, x, y):
        super().__init__(x, y)

    def update(self, dt, player_x, player_y, speed_chase, speed_patrol, stun):
        if stun > 0: return
        self.anim += dt
        dist = math.hypot(player_x - self.x, player_y - self.y)
        sees = dist < 250

        if sees:
            self.state = "chase"
            target_pos = (player_x, player_y)
        else:
            self.state = "patrol"
            if math.hypot(self.target[0] - self.x, self.target[1] - self.y) < 30:
                self.pick_random_patrol()
            target_pos = self.target

        self.path_timer -= dt
        if self.path_timer <= 0:
            self.path = self.find_path(target_pos[0], target_pos[1])
            self.path_timer = 0.3

        sp = speed_chase if self.state == "chase" else speed_patrol
        self.move_along_path(dt, sp)

    def draw(self, surf, cam_x, cam_y, stun):
        sx = int(self.x - cam_x);
        sy = int(self.y - cam_y)
        flip = self.facing_left

        def fx(offset):
            return sx + (offset if not flip else -offset)

        shadow = pygame.Surface((50, 16), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 130), (0, 0, 50, 16))
        surf.blit(shadow, (sx - 25, sy + 12))

        tail_wave = math.sin(self.anim * 8) * 8
        pygame.draw.lines(surf, (40, 40, 50), False, [
            (fx(-18), sy), (fx(-25), sy - 5), (fx(-32), sy - 12 + tail_wave)
        ], 5)

        step = math.sin(self.anim * 16) * 4
        pygame.draw.ellipse(surf, (30, 30, 40), (fx(-10 + step), sy + 6, 6, 12))
        pygame.draw.ellipse(surf, (30, 30, 40), (fx(5 - step), sy + 6, 6, 12))

        pygame.draw.ellipse(surf, (40, 40, 50), (fx(-16), sy - 10, 30, 20))
        pygame.draw.ellipse(surf, (70, 70, 80), (fx(-12), sy - 8, 24, 14))

        head_x = fx(18)
        head_y = sy - 12
        pygame.draw.circle(surf, (40, 40, 50), (head_x, head_y), 12)

        ear_wave = math.sin(self.anim * 8) * 2
        pygame.draw.polygon(surf, (40, 40, 50),
                            [(fx(10), head_y - 8), (fx(6), head_y - 22 + ear_wave), (fx(14), head_y - 10)])
        pygame.draw.polygon(surf, (40, 40, 50),
                            [(fx(26), head_y - 8), (fx(30), head_y - 22 - ear_wave), (fx(22), head_y - 10)])

        pygame.draw.ellipse(surf, (70, 70, 80), (head_x - 8, head_y + 2, 16, 10))

        pygame.draw.line(surf, (200, 200, 200), (fx(20), head_y + 4), (fx(30), head_y + 2), 1)
        pygame.draw.line(surf, (200, 200, 200), (fx(20), head_y + 6), (fx(30), head_y + 8), 1)

        eye_x = fx(22)
        eye_y = head_y - 2
        eye_col = (255, 50, 50) if self.state == "chase" else (200, 255, 100)
        pygame.draw.circle(surf, eye_col, (eye_x, eye_y), 4)
        pygame.draw.ellipse(surf, (0, 0, 0), (eye_x - 1, eye_y - 3, 2, 6))

        if stun > 0:
            for i in range(4):
                ang = pygame.time.get_ticks() / 200 + i * 1.57
                sx_off = head_x + math.cos(ang) * 18
                sy_off = head_y - 22 + math.sin(ang) * 5
                pygame.draw.circle(surf, (255, 255, 100), (int(sx_off), int(sy_off)), 3)


# ============ СОСТОЯНИЕ ============
game_scene = "lobby"
current_level = "street"
game_state = "playing"
flashlight_on = True
flashlight_battery = 180.0
FLASHLIGHT_MAX = 180.0
flashlight_drain = 1.0
flashlight_dead = False
shake = 0
message = ""
message_timer = 0
dog_start_delay = 20.0
teleport_cooldown = 0.0

is_nightmare = False
dog_speed_setting = 380


def get_grid(): return MAPS[current_level]["grid"]


def grid_h(): return len(get_grid())


def grid_w(): return len(get_grid()[0])


def is_wall_px(px, py):
    tx = int(px // TILE);
    ty = int(py // TILE)
    g = get_grid()
    if tx < 0 or ty < 0 or tx >= len(g[0]) or ty >= len(g):
        return True
    return g[ty][tx] == '1'


def get_free_positions(level):
    g = MAPS[level]["grid"]
    pos = []
    for y in range(len(g)):
        for x in range(len(g[0])):
            if g[y][x] in ('0', 'Y'):
                pos.append((x * TILE + TILE // 2, y * TILE + TILE // 2))
    return pos


def find_teleports(level, char):
    g = MAPS[level]["grid"]
    result = []
    for y in range(len(g)):
        for x in range(len(g[0])):
            if g[y][x] == char:
                result.append((x * TILE + TILE // 2, y * TILE + TILE // 2))
    return result


def find_safe_spawn(level, player_radius=14, prefer_far_from=None):
    g = MAPS[level]["grid"]
    candidates = []
    for ty in range(1, len(g) - 1):
        for tx in range(1, len(g[0]) - 1):
            if g[ty][tx] not in ('0', 'Y'): continue
            cx = tx * TILE + TILE // 2
            cy = ty * TILE + TILE // 2
            ok = True
            for dx, dy in [(-player_radius, 0), (player_radius, 0),
                           (0, -player_radius), (0, player_radius)]:
                px = cx + dx;
                py = cy + dy
                ptx = int(px // TILE);
                pty = int(py // TILE)
                if not (0 <= ptx < len(g[0]) and 0 <= pty < len(g)):
                    ok = False;
                    break
                if g[pty][ptx] == '1':
                    ok = False;
                    break
            if ok: candidates.append((cx, cy))
    if not candidates:
        for ty in range(len(g)):
            for tx in range(len(g[0])):
                if g[ty][tx] in ('0', 'Y'): return (tx * TILE + TILE // 2, ty * TILE + TILE // 2)
        return (TILE * 2, TILE * 2)
    if prefer_far_from:
        candidates.sort(key=lambda p: -math.hypot(p[0] - prefer_far_from[0], p[1] - prefer_far_from[1]))
        return candidates[0]
    random.shuffle(candidates)
    return candidates[0]


# ============ ПЕРЕМЕННЫЕ ИГРЫ ============
player_x, player_y = 0, 0
dog_obj = None
dog_level = "street"
cat_obj = None
cat_level = None

dog_stun = 0
dog_delay = 20.0
cat_stun = 0

parts = []
shotgun_count = 0
heli_count = 0
ammo = AMMO_TOTAL
door_pos = (0, 0)
heli_exit_pos = (0, 0)
cam_x, cam_y = 0, 0
player_anim = 0
player_dir = 0
player_moving = False
player_stamina = 100.0


def init_game():
    global player_x, player_y, dog_obj, dog_level, cat_obj, cat_level
    global dog_stun, dog_delay, cat_stun
    global parts, shotgun_count, heli_count, ammo, door_pos, heli_exit_pos, cam_x, cam_y, player_anim, player_dir, player_moving, player_stamina

    spawn_x, spawn_y = find_safe_spawn("street", player_radius=16)
    player_x, player_y = spawn_x, spawn_y
    player_stamina = 100.0

    dog_spawn = find_safe_spawn("street", player_radius=18, prefer_far_from=(spawn_x, spawn_y))
    dog_obj = Dog(dog_spawn[0], dog_spawn[1])
    dog_level = "street"
    dog_delay = dog_start_delay
    dog_stun = 0
    dog_obj.pick_random_patrol()

    if is_nightmare:
        cat_level = random.choice(["floor1", "floor2", "basement"])
        cat_spawn = find_safe_spawn(cat_level, player_radius=18)
        cat_obj = Cat(cat_spawn[0], cat_spawn[1])
        cat_stun = 0
        cat_obj.pick_random_patrol()
    else:
        cat_obj = None
        cat_level = None

    parts = []
    shotgun_count = 0
    heli_count = 0
    ammo = AMMO_TOTAL
    for level in ["floor1", "floor2", "basement"]:
        pos = get_free_positions(level)
        if len(pos) < 5: continue
        random.shuffle(pos)
        idx = 0
        parts.append({"x": pos[idx][0], "y": pos[idx][1], "kind": "shotgun", "level": level, "t": random.random() * 10})
        idx += 1
        for _ in range(4):
            if idx >= len(pos): break
            parts.append(
                {"x": pos[idx][0], "y": pos[idx][1], "kind": "heli", "level": level, "t": random.random() * 10})
            idx += 1

    dp = find_teleports("street", '5')
    if dp:
        door_pos = dp[0]
    else:
        door_pos = (TILE * 20 + TILE // 2, TILE * 14 + TILE // 2)

    street_free = get_free_positions("street")
    if street_free:
        random.shuffle(street_free)
        heli_exit_pos = street_free[0]
    cam_x, cam_y = 0, 0


# ============ ГЛАВНЫЙ ЦИКЛ ============
RUNNING = True
while RUNNING:
    dt = clock.tick(FPS) / 1000.0
    dt = min(dt, 0.05)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            RUNNING = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if game_scene == "playing":
                    game_scene = "lobby"
                else:
                    RUNNING = False
            if game_scene == "lobby":
                if event.key == pygame.K_RETURN:
                    generate_levels()
                    current_level = "street"
                    game_state = "playing"
                    flashlight_battery = FLASHLIGHT_MAX
                    flashlight_dead = False
                    flashlight_on = True
                    teleport_cooldown = 0.0
                    message = ""
                    message_timer = 0
                    init_game()
                    game_scene = "playing"
            else:
                if event.key == pygame.K_g and not flashlight_dead:
                    flashlight_on = not flashlight_on
                    message = "ФОНАРИК ВКЛ" if flashlight_on else "ФОНАРИК ВЫКЛ"
                    message_timer = 1.0
                if event.key == pygame.K_f and game_state == "playing":
                    nearest = None;
                    nearest_dist = 70
                    for p in parts:
                        if p["level"] == current_level:
                            d = math.hypot(p["x"] - player_x, p["y"] - player_y)
                            if d < nearest_dist: nearest_dist = d; nearest = p
                    if nearest:
                        parts.remove(nearest)
                        if nearest["kind"] == "shotgun":
                            shotgun_count += 1
                            ammo += AMMO_PER_SHOTGUN
                            message = f"+ ДРОБОВИК ({shotgun_count}/{SHOTGUN_TOTAL}) +1 ПАТРОН"
                        else:
                            heli_count += 1
                            message = f"+ ВЕРТОЛЁТ ({heli_count}/{HELI_TOTAL})"
                        message_timer = 1.5
                if event.key == pygame.K_SPACE and game_state == "playing":
                    if ammo <= 0:
                        message = "НЕТ ПАТРОНОВ!"
                        message_timer = 1.5
                    else:
                        if dog_level == current_level and dog_delay <= 0 and dog_stun <= 0:
                            dist = math.hypot(dog_obj.x - player_x, dog_obj.y - player_y)
                            if dist < 250:
                                ammo -= 1
                                dog_stun = 6.0
                                dog_obj.path = []
                                shake = 0.8
                                message = f"БАХ! ПЁС ОГЛУШЁН! (патронов: {ammo})"
                                message_timer = 2.0
                            else:
                                message = f"ПЁС ДАЛЕКО ({int(dist)} px)"
                                message_timer = 1.5
                        elif cat_obj and cat_level == current_level and cat_stun <= 0:
                            dist = math.hypot(cat_obj.x - player_x, cat_obj.y - player_y)
                            if dist < 250:
                                ammo -= 1
                                cat_stun = 6.0
                                cat_obj.path = []
                                shake = 0.8
                                message = f"БАХ! КОТ ОГЛУШЁН! (патронов: {ammo})"
                                message_timer = 2.0
                            else:
                                message = f"КОТ ДАЛЕКО ({int(dist)} px)"
                                message_timer = 1.5
                        else:
                            message = "ВРАГ НА ДРУГОМ ЭТАЖЕ ИЛИ СПИТ"
                            message_timer = 1.5

                if event.key == pygame.K_r and game_state in ("dead", "win"):
                    game_scene = "lobby"
        if event.type == pygame.MOUSEBUTTONDOWN and game_scene == "lobby":
            mx, my = event.pos
            y = 250 + 50
            speeds = [280, 380, 480, 580]
            for i, spd in enumerate(speeds):
                box = pygame.Rect(WIDTH // 2 - 300 + i * 155, y, 145, 50)
                if box.collidepoint(mx, my):
                    dog_speed_setting = spd
                    is_nightmare = (spd == 580)
            start_btn = pygame.Rect(WIDTH // 2 - 150, HEIGHT - 150, 300, 60)
            if start_btn.collidepoint(mx, my):
                generate_levels()
                current_level = "street"
                game_state = "playing"
                flashlight_battery = FLASHLIGHT_MAX
                flashlight_dead = False
                flashlight_on = True
                teleport_cooldown = 0.0
                message = ""
                message_timer = 0
                init_game()
                game_scene = "playing"

    if game_scene == "lobby":
        screen.fill((15, 15, 20))
        title = big_font.render("ОСОБНЯК", True, (200, 40, 40))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 80))
        sub = font.render("Выбери сложность и нажми ENTER чтобы начать", True, (150, 150, 150))
        screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 170))
        y = 250
        screen.blit(med_font.render("СЛОЖНОСТЬ (Скорость пса)", True, (255, 200, 100)), (WIDTH // 2 - 180, y))
        y += 50
        speeds = [("ЛЕГКО", 280), ("НОРМАЛЬНО", 380), ("СЛОЖНО", 480), ("КОШМАР (С КОТОМ)", 580)]
        for i, (name, spd) in enumerate(speeds):
            selected = (spd == dog_speed_setting)
            box_col = (200, 150, 50) if selected else (40, 40, 50)
            box = pygame.Rect(WIDTH // 2 - 300 + i * 155, y, 145, 50)
            pygame.draw.rect(screen, box_col, box, border_radius=6)
            if selected: pygame.draw.rect(screen, (255, 220, 120), box, 2, border_radius=6)
            txt = hint_font.render(name, True, (0, 0, 0) if selected else (200, 200, 200))
            screen.blit(txt, (box.centerx - txt.get_width() // 2, box.centery - txt.get_height() // 2))
        start_btn = pygame.Rect(WIDTH // 2 - 150, HEIGHT - 150, 300, 60)
        hover = start_btn.collidepoint(pygame.mouse.get_pos())
        col = (50, 200, 80) if hover else (30, 150, 60)
        pygame.draw.rect(screen, col, start_btn, border_radius=10)
        pygame.draw.rect(screen, (100, 255, 130), start_btn, 3, border_radius=10)
        btn_txt = med_font.render("НАЧАТЬ ИГРУ", True, (255, 255, 255))
        screen.blit(btn_txt,
                    (start_btn.centerx - btn_txt.get_width() // 2, start_btn.centery - btn_txt.get_height() // 2))
        pygame.display.flip()
        continue

    # ============ ЛОГИКА ИГРЫ ============
    if game_state == "playing":
        keys = pygame.key.get_pressed()

        # --- ДВИЖЕНИЕ ИГРОКА ---
        dx = dy = 0
        if keys[pygame.K_w] or keys[pygame.K_UP]: dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += 1

        sprinting = (keys[pygame.K_LSHIFT] and player_stamina > 0)
        speed = 170 * (1.55 if sprinting else 1.0)

        if sprinting:
            player_stamina -= 10.0 * dt
            if player_stamina < 0: player_stamina = 0
        else:
            player_stamina += (5.0 / 3.0) * dt
            if player_stamina > 100: player_stamina = 100

        player_moving = bool(dx or dy)
        if dx or dy:
            length = math.hypot(dx, dy)
            dx, dy = dx / length, dy / length
            player_dir = math.atan2(dy, dx)
            player_anim += dt * (14 if sprinting else 9)
        else:
            player_anim = 0

        nx = player_x + dx * speed * dt
        if not is_wall_px(nx + (13 if dx > 0 else -13), player_y): player_x = nx
        ny = player_y + dy * speed * dt
        if not is_wall_px(player_x, ny + (13 if dy > 0 else -13)): player_y = ny

        # --- ДВИЖЕНИЕ ПСА ---
        if dog_level == current_level:
            if dog_delay > 0:
                dog_delay -= dt
            else:
                if dog_stun > 0:
                    dog_stun -= dt
                else:
                    dog_obj.update(dt, player_x, player_y, dog_speed_setting, 0, 0)

        # --- ДВИЖЕНИЕ КОТА ---
        if cat_obj and cat_level == current_level:
            if cat_stun > 0:
                cat_stun -= dt
            else:
                cat_obj.update(dt, player_x, player_y, 450, 120, 0)

        # --- СМЕРТЬ И ПЕРЕХОДЫ ---
        if dog_level == current_level and dog_delay <= 0 and math.hypot(dog_obj.x - player_x,
                                                                        dog_obj.y - player_y) < 17 + 13:
            game_state = "dead";
            shake = 1.0
        if cat_obj and cat_level == current_level and math.hypot(cat_obj.x - player_x, cat_obj.y - player_y) < 15 + 13:
            game_state = "dead";
            shake = 1.0

        if teleport_cooldown > 0: teleport_cooldown -= dt
        if teleport_cooldown <= 0:
            g = get_grid()
            tx = int(player_x // TILE)
            ty = int(player_y // TILE)
            if 0 <= tx < len(g[0]) and 0 <= ty < len(g):
                cell = g[ty][tx]
                if cell == '2' or cell == '3':
                    new_lvl = {"floor1": "floor2", "basement": "floor1"}.get(current_level) if cell == '2' else {
                        "floor1": "basement", "floor2": "floor1"}.get(current_level)
                    if new_lvl:
                        current_level = new_lvl
                        tp = find_teleports(new_lvl, '3' if cell == '2' else '2')
                        if tp:
                            # ИСПРАВЛЕНИЕ: Ставим игрока В БЕЗОПАСНОЕ МЕСТО рядом с лестницей
                            safe_spot = find_safe_spawn(new_lvl, player_radius=16, prefer_far_from=tp[0])
                            player_x, player_y = safe_spot
                        if dog_level != new_lvl:
                            dog_level = new_lvl
                            ds = find_safe_spawn(new_lvl, 18, (player_x, player_y))
                            dog_obj.x, dog_obj.y = ds
                            dog_obj.path = []
                        message = f"ПЕРЕХОД НА {current_level.upper()}"
                        message_timer = 2.0
                        teleport_cooldown = 1.0
                elif cell == '4' and current_level != "street":
                    current_level = "street"
                    safe_spot = find_safe_spawn("street", player_radius=16, prefer_far_from=door_pos)
                    player_x, player_y = safe_spot
                    dog_level = "street"
                    ds = find_safe_spawn("street", 18, (player_x, player_y))
                    dog_obj.x, dog_obj.y = ds
                    dog_obj.path = []
                    message = "ВЫХОД НА УЛИЦУ"
                    message_timer = 2.0
                    teleport_cooldown = 1.0
                elif cell == '5' and current_level == "street":
                    current_level = "floor1"
                    tp = find_teleports("floor1", '4')
                    if tp:
                        safe_spot = find_safe_spawn("floor1", player_radius=16, prefer_far_from=tp[0])
                        player_x, player_y = safe_spot
                    dog_level = "floor1"
                    ds = find_safe_spawn("floor1", 18, (player_x, player_y))
                    dog_obj.x, dog_obj.y = ds
                    dog_obj.path = []
                    message = "ВХОД В ОСОБНЯК"
                    message_timer = 2.0
                    teleport_cooldown = 1.0

        if current_level == "street" and heli_count >= HELI_TOTAL:
            if math.hypot(heli_exit_pos[0] - player_x, heli_exit_pos[1] - player_y) < 50:
                game_state = "win"

    if message_timer > 0: message_timer -= dt

    # ============ РЕНДЕР ============
    screen.fill(BLACK)
    if current_level == "street": screen.fill(SKY_NIGHT)

    tx = player_x - WIDTH // 2
    ty = player_y - HEIGHT // 2
    cam_x += (tx - cam_x) * 0.15
    cam_y += (ty - cam_y) * 0.15
    max_x = grid_w() * TILE - WIDTH
    max_y = grid_h() * TILE - HEIGHT
    cam_x = max(0, min(cam_x, max_x)) if max_x > 0 else 0
    cam_y = max(0, min(cam_y, max_y)) if max_y > 0 else 0

    lvl_data = MAPS[current_level]
    g = lvl_data["grid"]

    for y in range(len(g)):
        for x in range(len(g[0])):
            rect = pygame.Rect(x * TILE - cam_x, y * TILE - cam_y, TILE, TILE)
            if rect.right < 0 or rect.bottom < 0 or rect.left > WIDTH or rect.top > HEIGHT: continue
            cell = g[y][x]
            seed = x * 100 + y
            if cell == '1':
                if lvl_data["wall"] == "brick":
                    draw_brick_wall(screen, rect, seed)
                elif lvl_data["wall"] == "fence":
                    draw_fence(screen, rect, seed)
                else:
                    draw_stone_wall(screen, rect, seed)
            else:
                if cell == 'Y':
                    draw_yard(screen, rect, seed)
                elif lvl_data["floor"] == "wood":
                    draw_wood_floor(screen, rect, seed)
                elif lvl_data["floor"] == "stone":
                    draw_stone_floor(screen, rect, seed)
                else:
                    draw_grass(screen, rect, seed)

                if cell == '2':
                    draw_stairs(screen, rect, True)
                elif cell == '3':
                    draw_stairs(screen, rect, False)
                elif cell == '4':
                    pygame.draw.rect(screen, (0, 200, 100), rect.inflate(-8, -8), 2)
                elif cell == '5':
                    draw_circular_entrance(screen, rect)

    for p in parts:
        if p["level"] == current_level:
            p["t"] += 0.05
            offset = math.sin(p["t"]) * 4
            color = PART_COLOR if p["kind"] == "shotgun" else PART_HELI
            sx = p["x"] - cam_x;
            sy = p["y"] - cam_y
            glow = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*color, 60), (30, 30), 28)
            screen.blit(glow, (sx - 30, sy - 30 + offset))
            pygame.draw.circle(screen, color, (int(sx), int(sy + offset)), 11)
            pygame.draw.circle(screen, (255, 255, 255), (int(sx), int(sy + offset)), 11, 2)
            t = hint_font.render("Д" if p["kind"] == "shotgun" else "В", True, BLACK)
            screen.blit(t, (sx - 5, sy - 7 + offset))

    if dog_level == current_level and dog_delay <= 0:
        dog_obj.draw(screen, cam_x, cam_y, dog_stun)

    if cat_obj and cat_level == current_level:
        cat_obj.draw(screen, cam_x, cam_y, cat_stun)

    sx = player_x - cam_x;
    sy = player_y - cam_y
    shadow = pygame.Surface((44, 18), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 120), (0, 0, 44, 18))
    screen.blit(shadow, (sx - 22, sy + 12))

    if flashlight_on and not flashlight_dead:
        fl = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        cone_pts = [(sx, sy)]
        for a in [-0.5, 0.5]:
            cone_pts.append((sx + math.cos(player_dir + a) * 160, sy + math.sin(player_dir + a) * 160))
        pygame.draw.polygon(fl, (255, 255, 200, 40), cone_pts)
        screen.blit(fl, (0, 0))

    walk = math.sin(player_anim) * 5 if player_moving else 0
    pygame.draw.ellipse(screen, (35, 50, 75), (sx - 10 - walk, sy + 8, 7, 12))
    pygame.draw.ellipse(screen, (35, 50, 75), (sx + 3 + walk, sy + 8, 7, 12))
    pygame.draw.ellipse(screen, (25, 45, 80), (sx - 11, sy - 8, 22, 22))
    pygame.draw.ellipse(screen, (45, 75, 125), (sx - 9, sy - 6, 18, 18))
    pygame.draw.circle(screen, (235, 195, 165), (sx, sy - 15), 10)
    pygame.draw.circle(screen, (45, 30, 20), (sx, sy - 18), 10)
    pygame.draw.circle(screen, (255, 255, 255), (sx - 3, sy - 15), 2)
    pygame.draw.circle(screen, (255, 255, 255), (sx + 3, sy - 15), 2)
    pygame.draw.circle(screen, (20, 20, 30), (sx - 3, sy - 15), 1)
    pygame.draw.circle(screen, (20, 20, 30), (sx + 3, sy - 15), 1)

    darkness = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    if flashlight_dead:
        darkness.fill((0, 0, 0, 235))
        pygame.draw.circle(darkness, (0, 0, 0, 0), (int(sx), int(sy)), 65)
    elif flashlight_on:
        darkness.fill((0, 0, 0, 200))
        pygame.draw.circle(darkness, (0, 0, 0, 0), (int(sx), int(sy)), 180)
    else:
        darkness.fill((0, 0, 0, 215))
        pygame.draw.circle(darkness, (0, 0, 0, 0), (int(sx), int(sy)), 100)
    screen.blit(darkness, (0, 0))

    # --- ИНТЕРФЕЙС (HUD) ---
    hud = pygame.Surface((WIDTH, 110), pygame.SRCALPHA)
    hud.fill((10, 10, 15, 180))
    screen.blit(hud, (0, 0))

    t1 = font.render(f"Дробовик: {shotgun_count}/{SHOTGUN_TOTAL}", True, (255, 200, 60))
    t2 = font.render(f"Вертолёт: {heli_count}/{HELI_TOTAL}", True, (100, 255, 150))
    screen.blit(t1, (20, 15))
    screen.blit(t2, (20, 45))

    pygame.draw.rect(screen, (40, 40, 40), (240, 22, 200, 18))
    stamina_w = int(200 * (player_stamina / 100))
    col_st = (110, 200, 255) if player_stamina > 20 else (255, 80, 80)
    pygame.draw.rect(screen, col_st, (240, 22, stamina_w, 18))
    st = hint_font.render("СТАМИНА (Shift)", True, (200, 220, 255))
    screen.blit(st, (240, 45))

    ax = WIDTH - 220;
    ay = HEIGHT - 60
    lbl_ammo = font.render(f"ПАТРОНЫ: {ammo}/{AMMO_TOTAL + SHOTGUN_TOTAL}", True, (255, 200, 120))
    screen.blit(lbl_ammo, (ax, ay - 25))
    for i in range(ammo):
        gx = ax + i * 22;
        gy = ay
        pygame.draw.rect(screen, (180, 120, 40), (gx, gy, 14, 26))
        pygame.draw.rect(screen, (255, 200, 80), (gx, gy, 14, 8))
        pygame.draw.rect(screen, (100, 60, 20), (gx, gy + 22, 14, 4))
        pygame.draw.rect(screen, (60, 40, 10), (gx, gy, 14, 26), 1)
    if ammo == 0:
        warn = tiny_font.render("ПУСТО — БЕГИ!", True, (255, 80, 80))
        screen.blit(warn, (ax, ay + 30))

    loc_names = {"street": "ДВОР", "floor1": "1 ЭТАЖ", "floor2": "2 ЭТАЖ", "basement": "ПОДВАЛ"}
    ltxt = med_font.render(f"[ {loc_names[current_level]} ]", True, (255, 255, 255))
    screen.blit(ltxt, (WIDTH - 350, 15))

    # --- МИНИКАРТА С ЗНАЧКАМИ ---
    MINIMAP_SIZE = 200
    MINIMAP_MARGIN = 15
    MINIMAP_TILE = MINIMAP_SIZE / MAP_W
    mm_w = int(grid_w() * MINIMAP_TILE)
    mm_h = int(grid_h() * MINIMAP_TILE)
    mm_x = WIDTH - mm_w - MINIMAP_MARGIN
    mm_y = MINIMAP_MARGIN + 105

    panel = pygame.Surface((mm_w + 10, mm_h + 30), pygame.SRCALPHA)
    panel.fill((5, 5, 12, 210))
    screen.blit(panel, (mm_x - 5, mm_y - 5))
    pygame.draw.rect(screen, (60, 60, 80), (mm_x - 5, mm_y - 5, mm_w + 10, mm_h + 30), 2)
    title = hint_font.render(f"🗺 {loc_names[current_level]}", True, (200, 220, 255))
    screen.blit(title, (mm_x, mm_y - 22))

    for y in range(len(g)):
        for x in range(len(g[0])):
            cell = g[y][x]
            rx = mm_x + x * MINIMAP_TILE
            ry = mm_y + y * MINIMAP_TILE
            if cell == '1':
                pygame.draw.rect(screen, (90, 90, 110), (rx, ry, MINIMAP_TILE + 1, MINIMAP_TILE + 1))
            else:
                col = (30, 50, 35) if current_level == "street" else (
                    (45, 45, 52) if current_level == "basement" else (55, 40, 30))
                pygame.draw.rect(screen, col, (rx, ry, MINIMAP_TILE + 1, MINIMAP_TILE + 1))
                if cell == '2':
                    pygame.draw.rect(screen, (200, 160, 80), (rx, ry, MINIMAP_TILE + 1, MINIMAP_TILE + 1))
                elif cell == '3':
                    pygame.draw.rect(screen, (140, 100, 50), (rx, ry, MINIMAP_TILE + 1, MINIMAP_TILE + 1))
                elif cell == '4':
                    pygame.draw.rect(screen, (0, 200, 100), (rx, ry, MINIMAP_TILE + 1, MINIMAP_TILE + 1))
                elif cell == '5':
                    pygame.draw.rect(screen, (80, 160, 255), (rx, ry, MINIMAP_TILE + 1, MINIMAP_TILE + 1))

    for p in parts:
        if p["level"] == current_level:
            px = mm_x + (p["x"] / TILE) * MINIMAP_TILE
            py = mm_y + (p["y"] / TILE) * MINIMAP_TILE
            base_col = ACID_SHOTGUN if p["kind"] == "shotgun" else ACID_HELI
            pygame.draw.circle(screen, base_col, (int(px), int(py)), 3)
            pygame.draw.circle(screen, (255, 255, 255), (int(px), int(py)), 1)

    if dog_level == current_level and dog_delay <= 0:
        dx = mm_x + (dog_obj.x / TILE) * MINIMAP_TILE
        dy = mm_y + (dog_obj.y / TILE) * MINIMAP_TILE
        pygame.draw.circle(screen, (255, 50, 50), (int(dx), int(dy)), 4)
        pygame.draw.circle(screen, (255, 255, 255), (int(dx), int(dy)), 4, 1)

    if cat_obj and cat_level == current_level:
        dx = mm_x + (cat_obj.x / TILE) * MINIMAP_TILE
        dy = mm_y + (cat_obj.y / TILE) * MINIMAP_TILE
        pygame.draw.circle(screen, (200, 50, 200), (int(dx), int(dy)), 4)
        pygame.draw.circle(screen, (255, 255, 255), (int(dx), int(dy)), 4, 1)

    px = mm_x + (player_x / TILE) * MINIMAP_TILE
    py = mm_y + (player_y / TILE) * MINIMAP_TILE
    pygame.draw.circle(screen, (110, 200, 255), (int(px), int(py)), 4)
    pygame.draw.circle(screen, (255, 255, 255), (int(px), int(py)), 4, 1)
    fx2 = px + math.cos(player_dir) * 6
    fy2 = py + math.sin(player_dir) * 6
    pygame.draw.line(screen, (255, 255, 255), (px, py), (fx2, fy2), 1)

    if current_level == "street":
        hx = mm_x + (heli_exit_pos[0] / TILE) * MINIMAP_TILE
        hy = mm_y + (heli_exit_pos[1] / TILE) * MINIMAP_TILE
        col = (0, 255, 100) if heli_count >= HELI_TOTAL else (255, 100, 100)
        pygame.draw.circle(screen, col, (int(hx), int(hy)), 4)
        pygame.draw.circle(screen, (255, 255, 255), (int(hx), int(hy)), 4, 1)

    if dog_level == current_level and dog_delay <= 0 and dog_stun <= 0 and dog_obj.state == "chase":
        col = (255, 40, 40) if int(pygame.time.get_ticks() / 200) % 2 == 0 else (130, 0, 0)
        ctxt = med_font.render("⚠ ПЁС ВИДИТ ТЕБЯ ⚠", True, col)
        screen.blit(ctxt, (WIDTH // 2 - 130, HEIGHT - 120))

    if message_timer > 0:
        m = font.render(message, True, (255, 255, 100))
        screen.blit(m, (WIDTH // 2 - m.get_width() // 2, HEIGHT - 150))

    if game_state == "dead":
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((40, 0, 0, 220))
        screen.blit(overlay, (0, 0))
        txt = big_font.render("ТЕБЯ РАЗОРВАЛИ", True, (255, 40, 40))
        screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 100))
        rtxt = font.render("R — в лобби  |  ESC — выход", True, (255, 255, 255))
        screen.blit(rtxt, (WIDTH // 2 - rtxt.get_width() // 2, HEIGHT // 2 + 80))
    elif game_state == "win":
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 30, 10, 220))
        screen.blit(overlay, (0, 0))
        txt = big_font.render("ТЫ СБЕЖАЛ!", True, (100, 255, 150))
        screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 100))
        rtxt = font.render("R — в лобби  |  ESC — выход", True, (255, 255, 255))
        screen.blit(rtxt, (WIDTH // 2 - rtxt.get_width() // 2, HEIGHT // 2 + 80))

    if shake > 0:
        shake -= dt * 2
        if shake > 0:
            sxx = random.randint(-8, 8)
            syy = random.randint(-8, 8)
            tmp = screen.copy()
            screen.fill(BLACK)
            screen.blit(tmp, (sxx, syy))

    pygame.display.flip()

pygame.quit()
sys.exit()


