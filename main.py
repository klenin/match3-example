import pygame as pg
from pygame.math import Vector2
import math

from game import *

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
        CellType.ONYX: (0, 0, 50),
        CellType.QUARTZ: (255, 255, 0),
    }
    SWAP_TIME = 0.3
    FALL_TIME = 0.4

    def __init__(self, field):
        self.field = field
        self.screen = pg.display.set_mode((640, 480))
        self.font = pg.font.SysFont("Arial", 20)
        self.cell_down = None
        self.set_state(State.NORMAL)
        self.flying_time = 0
        self.flying = dict()
        self.thinking_start = 0

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
            pg.draw.line(surface, Colors.GRID, (p.x, self.BOARD_POS.y), (p.x, last.y), 2)
            pg.draw.line(surface, Colors.GRID, (self.BOARD_POS.x, p.y), (last.x, p.x), 2)

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
        surface.blit(self._write(f"Turn: {field.turn}"), (20, 45))

    def draw(self):
        background = pg.Surface(self.screen.get_size())
        background.fill((255, 255, 255))
        self.draw_grid(background)
        self.draw_gems(background)
        self.draw_score(background)
        self.screen.blit(background.convert(), (0, 0))

    def start_swapping(self, a, b):
        ui.set_state(State.SWAPPING)
        ui.flying[v2int(a)] = Vector2(b)
        ui.flying[v2int(b)] = Vector2(a)
        ui.flying_time = UI.SWAP_TIME

    def start_falling(self):
        ui.set_state(State.FALLING)
        ui.flying_time = ui.FALL_TIME
        ui.falling_gems = self.field.make_fall()
        ui.flying = dict(ui.falling_gems)

FPS = 60

#rnd.seed(273426)
pg.init()
clock = pg.time.Clock()
field = Field(LEVELS[3], rnd.Random())
#field = History.load_field(LEVELS[3], "level.json")
ui = UI(field)
ai = AI(field)
history = History("Vasya", field, level=2)

mainloop = True
global_time = 0

while mainloop:
    delta = clock.tick(FPS)
    global_time += delta / 1000
    
    for event in pg.event.get():
        if event.type == pg.QUIT or event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
            mainloop = False
            break
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            ui.cell_down = UI.pos_to_cell(event.pos)
        if ui.state == State.NORMAL and ui.is_clicked(event):
            ui.set_state(State.CELL_SELECTED)
            ui.selected_cell = ui.cell_down
        elif ui.state == State.NORMAL and event.type == pg.KEYDOWN and event.key == 97:
            m = ai.make_random_move()
            if m:
                ui.cell_down, ui.selected_cell = m
                ui.start_swapping(*m)
        elif ui.state == State.NORMAL and event.type == pg.KEYDOWN and event.key == 65:
            m = ai.make_good_move()
            if m:
                ui.cell_down, ui.selected_cell = m
                ui.start_swapping(*m)

        elif ui.state == State.CELL_SELECTED and ui.is_clicked(event):
            if ui.cell_down == ui.selected_cell:
                ui.set_state(State.NORMAL)
            elif field.can_swap(ui.cell_down, ui.selected_cell):
                ui.start_swapping(ui.cell_down, ui.selected_cell)
            else:
                ui.selected_cell = ui.cell_down
        
    if ui.state == State.SWAPPING and ui.state_time > ui.flying_time:
        history.moves.append((v2int(ui.cell_down), v2int(ui.selected_cell)))
        history.times.append(global_time - ui.thinking_start)
        field.apply_move(ui.cell_down, ui.selected_cell)
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
            ui.thinking_start = global_time

    ui.state_time += delta / 1000
    ui.draw()
    pg.display.flip()

history.save()
pg.quit()
