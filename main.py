import pygame as pg
from pygame.math import Vector2
from enum import Enum
import random as rnd
import math
import copy
import json

class CellType:
    EMPTY = 0
    RUBY = 1
    EMERALD = 2
    DIAMOND = 3
    AMBER = 4
    BERYL = 5
    NORMAL_SET = [RUBY, EMERALD, DIAMOND, AMBER, BERYL]

def v2int(v): return int(v.x), int(v.y)

class History:
    def __init__(self, name, field):
        self.name = name
        self.field = copy.deepcopy(field)
        self.moves = []

    def save(self):
        with open("history.log", "w") as f:
            f.write(json.dumps({ 'name': self.name, 'field': self.field.cells, 'moves': self.moves }))

class Field:
    SIZE = 9
    MIN_EXPLODE = 3

    def __init__(self):
        self.score = 0
        self.cells = self._full_random()
        while self.explode_all():
            self.apply_fall(self.make_fall())
            self.fill()
        self.score = 0
 
    def _init_by_retries(self):
        while True:
            self.cells = self._full_random()
            any, _ = self.maybe_explode_all()
            if not any: break
    
    def _full_random(self):
        return [ rnd.choices(CellType.NORMAL_SET, k=Field.SIZE) for _ in range(Field.SIZE) ]

    @staticmethod
    def is_inside(pos):
        return 0 <= pos.x < Field.SIZE and 0 <= pos.y < Field.SIZE

    def can_swap(self, a, b):
        p = a - b
        if abs(p.x) + abs(p.y) != 1: return False
        f = copy.deepcopy(self)
        f.swap(a, b)
        return f.is_exploding(int(a.x), int(a.y)) or f.is_exploding(int(b.x), int(b.y))
    
    def swap(self, a, b):
        a, b = map(v2int, [a, b])
        self.cells[a[1]][a[0]], self.cells[b[1]][b[0]] = self.cells[b[1]][b[0]], self.cells[a[1]][a[0]]

    def is_exploding(self, x, y):
        color = self.cells[y][x]
        def count(dx, dy):
            xx = x; yy = y; cnt = 0
            while self.is_inside(Vector2(xx, yy)) and self.cells[yy][xx] == color:
                xx += dx; yy += dy
                cnt += 1
            return cnt
        return (
            count(1, 0) + count(-1, 0) - 1 >= self.MIN_EXPLODE or
            count(0, 1) + count(0, -1) - 1 >= self.MIN_EXPLODE)

    def make_fall(self):
        result = []
        for x in range(Field.SIZE):
            i = Field.SIZE - 1
            for y in range(Field.SIZE - 1, -1, -1):
                if self.cells[y][x] != CellType.EMPTY:
                    if y < i:
                        result.append(((x, y),(x, i)))
                    i -= 1
        return result

    def apply_fall(self, fall):
        for src, dst in fall:
            self.cells[dst[1]][dst[0]] = self.cells[src[1]][dst[0]]
            self.cells[src[1]][dst[0]] = CellType.EMPTY
    
    def maybe_explode_all(self):
        explodes = [ [False] * Field.SIZE for _ in range(Field.SIZE) ]
        cnt = 1; score = 0
        for y in range(Field.SIZE):
            for x in range(1, Field.SIZE + 1):
                if (
                    x < Field.SIZE and self.cells[y][x] != CellType.EMPTY and
                    self.cells[y][x] == self.cells[y][x - 1]
                ):
                    cnt += 1
                else:
                    if cnt >= self.MIN_EXPLODE:
                        for i in range(x - cnt, x):
                            explodes[y][i] = True
                        score += cnt
                    cnt = 1
        cnt = 1
        for x in range(Field.SIZE):
            for y in range(1, Field.SIZE + 1):
                if (
                    y < Field.SIZE and self.cells[y][x] != CellType.EMPTY and
                    self.cells[y][x] == self.cells[y - 1][x]
                ):
                    cnt += 1
                else:
                    if cnt >= self.MIN_EXPLODE:
                        for i in range(y - cnt, y):
                            explodes[i][x] = True
                        score += cnt
                    cnt = 1
        return score, explodes

    def explode_all(self):
        score, explodes = self.maybe_explode_all()
        if score:
            for y in range(Field.SIZE):
                for x in range(Field.SIZE):
                    if explodes[y][x]:
                        self.cells[y][x] = CellType.EMPTY
        self.score += score
        return score

    def fill(self):
        for y in range(Field.SIZE):
            for x in range(Field.SIZE):
                if self.cells[y][x] == CellType.EMPTY:
                    self.cells[y][x] = rnd.choice(CellType.NORMAL_SET)

class Colors:
    GRID = (128, 128, 128)

class State(Enum):
    NORMAL = 1
    CELL_SELECTED = 2
    SWAPPING = 3
    EXPLODING = 4
    FALLING = 5

class UI:
    BOARD_POS = Vector2(100, 100)
    CELL_SIZE = Vector2(33, 33)
    CELL_COLORS = {
        CellType.EMPTY: (255, 255, 255),
        CellType.RUBY: (255, 0, 0),
        CellType.EMERALD: (0, 255, 00),
        CellType.DIAMOND: (0, 0, 255),
        CellType.AMBER: (255, 150, 100),
        CellType.BERYL: (128, 200, 255),
    }
    SWAP_TIME = 0.6
    FALL_TIME = 0.8

    def __init__(self, field):
        self.field = field
        self.screen = pg.display.set_mode((640, 480))
        self.font = pg.font.SysFont("Arial", 20)
        self.cell_down = None
        self.set_state(State.NORMAL)
        self.flying_time = 0
        self.flying = dict()

    @staticmethod
    def pos_to_cell(pos):
        return (pos - UI.BOARD_POS).elementwise() // UI.CELL_SIZE
    
    def is_clicked(self, event):
        return (event.type == pg.MOUSEBUTTONUP and event.button == 1 and
            self.pos_to_cell(event.pos) == self.cell_down and Field.is_inside(self.cell_down))
    
    def set_state(self, state):
        self.state = state
        self.state_time = 0

    def draw_grid(self, surface):
        last = self.BOARD_POS + self.CELL_SIZE * Field.SIZE
        for i in range(Field.SIZE + 1):
            p = self.BOARD_POS + self.CELL_SIZE * i
            pg.draw.line(surface, Colors.GRID, (p.x, self.BOARD_POS.y), (p.x, last.y), width=2)
            pg.draw.line(surface, Colors.GRID, (self.BOARD_POS.x, p.y), (last.x, p.x), width=2)

    def draw_gems(self, surface):
        MARGIN = 3
        for y in range(Field.SIZE):
            for x in range(Field.SIZE):
                if self.field.cells[y][x] == CellType.EMPTY:
                    continue
                color = self.CELL_COLORS[self.field.cells[y][x]]
                p = Vector2(x, y)
                if self.state in [State.SWAPPING, State.FALLING] and (x, y) in ui.flying:
                    dest = ui.flying[(x, y)]
                    p = p.lerp(dest, min(ui.state_time / ui.flying_time, 1.0))
                p = self.BOARD_POS + self.CELL_SIZE.elementwise() * p
                delta_r = MARGIN
                if self.state == State.CELL_SELECTED and (x, y) == ui.selected_cell:
                    delta_r = math.sin(ui.state_time * 5) + 2
                dr = Vector2(delta_r)
                pg.draw.ellipse(surface, color, (p + dr, self.CELL_SIZE - 2 * dr + Vector2(1)))

    def _write(self, text):
        return self.font.render(text, True, (0, 0, 0)).convert_alpha()

    def draw_score(self, surface):
        surface.blit(self._write(f"Score: {field.score}"), (20, 20))

    def draw(self):
        background = pg.Surface(self.screen.get_size())
        background.fill((255, 255, 255))
        self.draw_grid(background)
        self.draw_gems(background)
        self.draw_score(background)
        self.screen.blit(background.convert(), (0, 0))

    def start_falling(self):
        ui.set_state(State.FALLING)
        ui.flying_time = ui.FALL_TIME
        ui.falling_gems = self.field.make_fall()
        ui.flying = dict(ui.falling_gems)

FPS = 60

#rnd.seed(273426)
pg.init()
clock = pg.time.Clock()
field = Field()
ui = UI(field)
history = History("Vasya", field)

mainloop = True

while mainloop:
    delta = clock.tick(FPS)
    
    for event in pg.event.get():
        if event.type == pg.QUIT or event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
            mainloop = False
            break
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            ui.cell_down = UI.pos_to_cell(event.pos)
        if ui.state == State.NORMAL and ui.is_clicked(event):
            ui.set_state(State.CELL_SELECTED)
            ui.selected_cell = ui.cell_down
        elif ui.state == State.CELL_SELECTED and ui.is_clicked(event):
            if ui.cell_down == ui.selected_cell:
                ui.set_state(State.NORMAL)
            elif field.can_swap(ui.cell_down, ui.selected_cell):
                ui.set_state(State.SWAPPING)
                ui.flying[v2int(ui.cell_down)] = ui.selected_cell
                ui.flying[v2int(ui.selected_cell)] = ui.cell_down
                ui.flying_time = UI.SWAP_TIME
            else:
                ui.selected_cell = ui.cell_down
        
    if ui.state == State.SWAPPING and ui.state_time > ui.flying_time:
        history.moves.append((v2int(ui.cell_down), v2int(ui.cell_down)))
        field.swap(ui.cell_down, ui.selected_cell)
        field.explode_all()
        ui.start_falling()
    elif ui.state == State.FALLING and ui.state_time >= ui.flying_time:
        field.apply_fall(ui.falling_gems)
        field.fill()
        if field.explode_all():
            ui.start_falling()
        else:
            ui.set_state(State.NORMAL)
            ui.flying.clear()
            ui.flying_time = 0

    ui.state_time += delta / 1000
    ui.draw()
    pg.display.flip()

history.save()
pg.quit()
